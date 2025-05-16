# Python file to validate a full paththrough
# Everything should be automated through this file
import argparse
import glob
import json
import os
import sys
import time
import multiprocessing as mp
from multiprocessing import Process
import pathlib

from helpers.ollama_helper_tester import OllamaHelper
from helpers.py_pi_query import PyPIQuery
from helpers.build_dockerfile import DockerHelper
from helpers.deps_scraper import DepsScraper

SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
os.chdir(SCRIPT_DIR)

def _say(msg, *, interactive: bool):
    """Print only when NOT in interactive mode."""
    if not interactive:
        print(msg)

def _apply_user_patch(user_input: str, llm_eval: dict) -> dict:
        """
        Very small command language:
        <Enter>           → do nothing
        q / quit          → abort program
        py==3.9           → force python_version
        mod==ver          → add / override module version
        del mod           → remove module
        Multiple commands separated by ','.
        """
        user_input = user_input.strip()
        if not user_input:
            return llm_eval                      # nothing to change

        if user_input.lower() in {"q", "quit"}:
            print("👋  Stopping on user request."); sys.exit(0)

        for cmd in user_input.split(","):
            cmd = cmd.strip()
            if cmd.startswith("py=="):
                llm_eval["python_version"] = cmd.split("==", 1)[1]
            elif cmd.startswith("del "):
                llm_eval["python_modules"].pop(cmd.split(None, 1)[1].strip(),
                                            None)
            elif "==" in cmd:
                mod, ver = [x.strip() for x in cmd.split("==", 1)]
                llm_eval["python_modules"][mod] = ver
            # ignore unknown spellings
        return llm_eval

_BUILTIN = {
    # python ≥3.10 →  sys.stdlib_module_names  (but keep a static fallback)
    "sys", "getopt", "os", "re", "json", "typing", "argparse", "pathlib",
}

def _is_builtin(mod: str) -> bool:
    """True if `mod` is in the std‑lib – never pip‑install these."""
    import sys
    if hasattr(sys, "stdlib_module_names"):           # 3.10+
        return mod in sys.stdlib_module_names
    return mod in _BUILTIN

def _summarise_error_with_llm(raw_log: str, model: str) -> str:
    """
    Ask the local Ollama model for a concise diagnosis **and** an actionable
    recommendation that matches the interactive grammar:
        <Enter> | py==3.x | mod==ver | del mod | q
    """
    import subprocess, textwrap, json, shlex

    # include the *whole* log – the model will pick what it needs
    log_tail = raw_log.strip()

    # Give the LLM a tiny bit of world‑knowledge it usually lacks:
    # built‑in modules must not be installed with pip.
    builtin_hint = ", ".join(sorted(_BUILTIN))

    prompt = textwrap.dedent(f"""
        You are an expert Python dependency troubleshooter.

        ## Context
        • The following is the full docker build / run log:

        ```log
        {log_tail}
        ```

        • The standard‑library modules **must never be installed with pip**.
          They include: {builtin_hint} …

        • The shell UI the user sees offers ONLY these commands
          ( anything else will be ignored ):
               ↩ <Enter>    = retry unchanged
               py==x.y      = force Python version
               pkg_name==v  = pin pkg to version v
               del pkg      = remove pkg from requirements
               q | quit     = abort

        ## Your task
        1. Detect the *error type* (ImportError, VersionNotFound, etc.).
        2. Copy the ONE most relevant log line into **KEY_MESSAGE**.
        3. Summarise why it failed.
        4. Analyse.
        5. Recommend *one* concrete next command that fits the grammar above.
           • If the package is std‑lib (e.g. getopt, sys) → recommend `del getopt`.
           • If a version that is not built-in is missing → recommend e.g.`pillow==6.0.0`.
           • If Python version mismatch → recommend `py==<suggested‑version>`.
           • If the error type is a syntax error → recommend changing Python version (e.g. `py==2.7`) or manual examination.

        ## Output format – five single‑line fields, exactly this order
        ERROR_TYPE: …
        KEY_MESSAGE: …
        SUMMARY: …
        ANALYSIS: …
        RECOMMENDATION: …
    """).strip()

    try:
        out = subprocess.check_output(
            ["ollama", "run", model, prompt],
            text=True, timeout=60
        )
        # keep first 5 non‑blank lines (in case the LLM adds extras)
        lines = [ln.strip() for ln in out.splitlines() if ln.strip()]
        return "\n".join(lines[:5])
    except subprocess.SubprocessError as e:
        return f"(could not get LLM summary – {e})"

# helper to obtain a clean model‑name for the CLI
def _clean_ollama_tag(raw: object) -> str:
    """
    Accepts whatever LangChain / your helper stores (`ChatOllama`, a dict,
    or a long string with params) and returns just   gemma3:4b-it-qat
    """
    if hasattr(raw, "model_name"):
        raw = raw.model_name                    # ChatOllama object
    raw = str(raw)                              # make sure it is a str

    # remove leading “model=” if present, then take first token
    tag = raw.replace("model=", "").split()[0]
    # strip quotes that the helper inserts
    return tag.strip("\"'")

class TestExecutor():

    def __init__(self, base_url="http://localhost:11434", model='gemma2', logging=True, temp=0.7, end_loop=5, search_range=1, base_modules='./modules') -> None:
        # Initiate instance of Ollama helper and PyPi Query
        print(f'Running model- {model} with temp {temp}. Looping {end_loop} times with a search range of {search_range}')
        self.ollama_helper = OllamaHelper(base_url=base_url, model=model, logging=logging, temp=temp, base_modules=base_modules)
        self.pypi = PyPIQuery(logging=logging, base_modules=base_modules)
        self.deps = DepsScraper(logging=logging)
        self.end_loop = end_loop
        self.search_range = search_range
        self.start_time = time.time()
        pass

    # Defines JSONObject dictionary for dot notation
    def validate_json(self, json_string):
        try:
            json.loads(json_string)
        except ValueError as err:
            return False
        return True

    # Reads the contents of the given file
    def read_python_file(self, file):
        with open(file, 'r') as file:
            data = file.read().replace('\n', '')
        return data

    def evaluate_file(self, llm, file):
        # First LLM pass- Evaluates the Python file and gives us the initial JSON
        llm_eval = llm.evaluate_file(file)
        llm_eval['python_version'] = str(llm_eval['python_version'])

        # Should normally be a list. Re-format to a list if it is a dict.
        python_modules = llm_eval['python_modules']
        if type(python_modules) == dict:
            list_modules = []
            for module in python_modules:
                list_modules.append(module)
            llm_eval['python_modules'] = list_modules

        return llm_eval

    def get_module_specifics(self, llm, llm_eval):
        # Uses the modules from the LLM output to get a specific set of versions for the inferred Python version
        # Also returns an updated python version, based on what the model had provided
        llm_eval['python_modules'], llm_eval['python_version'] = llm.pypi.get_module_specifics(llm_eval)
        
        module_versions = llm.get_module_versions(llm_eval)
        llm_eval['python_modules'] = module_versions

        return llm_eval

    def build_container(self, dockerHelper, llm, llm_eval, file, error_details = {}, interactive=False):
        # Build the docker image with the given JSON and file/ paths
        dockerHelper.create_dockerfile(llm_eval, file)
        passed, docker_build_output = dockerHelper.build_dockerfile(file)
        if not passed:
            _say(docker_build_output, interactive=interactive)
            output, error_type = llm.process_error(docker_build_output, error_details, llm_eval)
            print(f"docker build failed!")
            return False, docker_build_output, output, error_type
        else:
            print(f"docker build complete!")
            return True, docker_build_output, None, None

    # Handle and update modules and versions that have previously had errors
    # Updates the 'error_modules' list to feed back ot the model later
    def naughty_bois(self, module, error_handler, error_type, llm_eval):
        error_handler[error_type] += 1
        error_handler['previous'] = error_type

        if module != None and module['module'] in llm_eval['python_modules']:
            if module['module'] in error_handler['error_modules']:
                error_handler['error_modules'][module['module']].append(llm_eval['python_modules'][module['module']])
            else:
                error_handler['error_modules'][module['module']] = [llm_eval['python_modules'][module['module']]]
        else:
            print('No unresolved modules this time.')

        return error_handler


    # Update the llm details
    # Set previous modules, so our output is correct
    # Removes and adds modules based on the new module returned by the LLM
    def update_llm_eval(self, new, llm_eval):
        details = llm_eval.copy()
        details['previous_python_modules'] = details['python_modules'].copy()
        if new != None:
            module_name = self.pypi.check_module_name(new['module'])
            module_name = module_name[0] if len(module_name) > 0 else module_name
            # Check to see if we need to pop a module or add the new version
            if new['version'] == None or new['version'] == 'None' or new['version'] == 'none' or new['version'] == '' and module_name in details['python_modules']:
                details['python_modules'].pop(module_name)
            else:
                details['python_modules'][module_name] = new['version']
        return details
        
    # Append module to the given list
    def append_module(self, module_name, list):
        return module_name in list
    
    # Method to shuffle the dependencies
    # This is to ensure dependencies are installed in the correct order
    def shuffle_modules(self, new_module, move_module, llm_details):
        modules = []
        python_modules = llm_details['python_modules'].copy()
        for module in python_modules:
            if module == move_module:
                if not self.append_module(new_module, modules): modules.append(new_module)
                if not self.append_module(move_module, modules): modules.append(move_module)
            else:
                if not self.append_module(module, modules): modules.append(module)

        llm_details['python_modules'] = {module: python_modules[module] for module in modules}
        return llm_details

    # Main docker process loop
    # This method is given as a process to run in parallel with each other
    # Handles the main loop of building | running | validating
    def docker_create_process(self, ollama_helper, llm_eval, file, process_num, interactive=False):
        # Create the YAML file in the same folder as the snippet
        dockerHelper = DockerHelper(logging=not interactive)

        # Get a set of modules, based on the evaluation
        # Also pull down working versions from PyPi at the same time.
        llm_eval = self.get_module_specifics(ollama_helper, llm_eval)

        # print(llm_eval)
        _say(llm_eval, interactive=interactive)

        # Dictionary to store erroring module versions and keep a list of error types
        error_handler = {
            'previous': '',
            'error_modules': {},
            'ImportError': 0,
            'ModuleNotFound': 0,
            'VersionNotFound': 0,
            'DependencyConflict': 0,
            'AttributeError': 0,
            'NonZeroCode': 0,
            'SyntaxError': 0,
        }

        # Get the project folder so we can write out our data file
        project_dir, dir_name, project_file = dockerHelper.get_project_dir(file)
        # File to open is unique based on the python version
        if interactive:
            file_to_open = f"{project_dir}/output_data_interactive.yml"
        else:
            file_to_open = f"{project_dir}/output_data_{llm_eval['python_version']}.yml"

        # Output to the log file
        output_file = open(file_to_open, "a")
        output_file.write('---\n')
        output_file.write(f"python_version: {llm_eval['python_version']}\n")
        output_file.write(f"start_time: {self.start_time}\n")
        output_file.write('iterations:\n')
        output_file.close()
        # Build loop
        run_complete = False
        build_complete = False
        # job_complete = False
        loop = 1

        while not run_complete:
            error = ''
            try:
                # print(f"In process {process_num}")
                _say(f"In process {process_num}", interactive=interactive)
                # time.sleep(5)
                # Main build loop
                while not build_complete:
                    # Build the container and report any error that may occur during the build
                    # Returns if the build completed, docker output (error), output (details from the LLM) and the error type
                    build_complete, docker_output, output, error_type = self.build_container(dockerHelper, ollama_helper, llm_eval, file, error_handler, interactive=interactive)
                    # If the build failed, handle the error

                    # SUCCESS: in interactive mode we are done once
                    # the Docker image is built without errors.
                    if build_complete and interactive:
                        print("\n✅  Dependency resolution finished – "
                              "Dockerfile built successfully.\n"
                              "You can now run the container.  Bye!")
                        dockerHelper.delete_image()   # optional cleanup
                        sys.exit(0)
                    if not build_complete:
                        # Update error_handler with any failing module and version
                        error_handler = self.naughty_bois(output, error_handler, error_type, llm_eval)
                        # Update the LLM details with the information from the build ouput
                        llm_eval = self.update_llm_eval(output, llm_eval)
                        # If we had an import error, and a non zero code, then we may have an ordering issue and need to reshuffle the modules
                        if error_type == 'ImportError' and 'returned a non-zero code: 1' in docker_output:
                            zero_code_module = ollama_helper.non_zero_error(docker_output)
                            llm_eval = self.shuffle_modules(output['module'], zero_code_module, llm_eval)
                        # Given a Non Zero and PATH environment in the output, remove this module as it may be completely erroneous
                        if error_type == 'NonZeroCode' and 'PATH environment' in docker_output:
                            llm_eval['python_modules'].pop(output['module'])

                        # Persist state and, in interactive mode, pause here
                        loop = self.end_test(file_to_open, llm_eval, dockerHelper, error_type, docker_output, loop, False)

                        if interactive and not run_complete:
                            short_log = docker_output if isinstance(docker_output, str) else str(docker_output)
                            tag       = _clean_ollama_tag(ollama_helper.model)
                            summary   = _summarise_error_with_llm(short_log, tag)
                            print("\n🧠  " + summary.replace("\n", "\n🧠  ") + "\n")
                            ui = input(
                                f"↩ <Enter>=retry │ py==x.y  │ mod==ver  │ "
                                f"del mod  │ q=quit » ")
                            llm_eval = _apply_user_patch(ui, llm_eval)

                            continue

                # while not run_complete:
                docker_output = dockerHelper.run_container_test()
                print(docker_output)

                # Processes Docker run information (after a build has been successul we must run it to see if everything is correct)
                output, error_type = ollama_helper.process_error(docker_output, error_handler, llm_eval)
                
                # Direct the flow to the correct error logging method
                if 'ImportError' in error_type:
                    if 'DJANGO_SETTINGS_MODULE is undefined' in docker_output:
                        run_complete = True
                        llm_eval = self.update_llm_eval(output, llm_eval)
                    else:
                        build_complete = False
                        error_handler = self.naughty_bois(output, error_handler, error_type, llm_eval)
                        llm_eval = self.update_llm_eval(output, llm_eval)
                elif 'VersionNotFound' in error_type:
                    build_complete = False
                    error_handler = self.naughty_bois(output, error_handler, error_type, llm_eval)
                    llm_eval = self.update_llm_eval(output, llm_eval)
                elif 'DependencyConflict' in error_type:
                    build_complete = False
                    error_handler = self.naughty_bois(output, error_handler, error_type, llm_eval)
                    llm_eval = self.update_llm_eval(output, llm_eval)
                elif 'ModuleNotFound' in error_type:
                    build_complete = False
                    error_handler = self.naughty_bois(output, error_handler, error_type, llm_eval)
                    llm_eval = self.update_llm_eval(output, llm_eval)
                elif 'AttributeError' in error_type:
                    build_complete = False
                    error_handler = self.naughty_bois(output, error_handler, error_type, llm_eval)
                    llm_eval = self.update_llm_eval(output, llm_eval)
                elif 'InvalidVersion' in error_type:
                    build_complete = False
                    error_handler = self.naughty_bois(output, error_handler, error_type, llm_eval)
                    llm_eval = self.update_llm_eval(output, llm_eval)
                elif 'NonZeroCode' in error_type:
                    build_complete = False
                    error_handler = self.naughty_bois(output, error_handler, error_type, llm_eval)
                    if output['module'] in llm_eval['python_modules']:
                        llm_eval['python_modules'].pop(output['module'])
                elif 'SyntaxError' in error_type:
                    build_complete = False
                    # ── Interactive pause on SyntaxError ────────────────
                    if interactive and not run_complete:
                        short_log = str(docker_output)
                        tag       = _clean_ollama_tag(ollama_helper.model)
                        summary   = _summarise_error_with_llm(short_log, tag)
                        print("\n🧠  " + summary.replace("\n", "\n🧠  ") + "\n")
                        ui = input(
                            "↩ <Enter>=retry │ py==x.y │ mod==ver │ del mod │ q=quit » ")
                        llm_eval = _apply_user_patch(ui, llm_eval)
                        # user may just press <Enter>; either way we stop here
                        # and let the outer while-loop restart a fresh build.
                    build_complete = False
                    error_handler = self.naughty_bois(output, error_handler, error_type, llm_eval)
                    llm_eval = self.update_llm_eval(output, llm_eval)
                elif 'NameError' in error_type:
                    run_complete = True
                    error_handler = self.naughty_bois(output, error_handler, error_type, llm_eval)
                    llm_eval = self.update_llm_eval(output, llm_eval)
                elif 'None' in error_type:
                    run_complete = True
                    llm_eval = self.update_llm_eval(None, llm_eval)
            except Exception as e:
                print(f"Failed to build container: {e}")
            # Update the loop number and log the details to the log file
            loop = self.end_test(file_to_open, llm_eval, dockerHelper, error_type, docker_output, loop, run_complete)
        
        # If we've left the while loop then we need to make sure everything is killed correctly
        loop = self.end_loop
        # Update the loop number and log the details to the log file
        self.end_test(file_to_open, llm_eval, dockerHelper, error_type, docker_output, loop, True)

    # Logging specific, ensures correct spaces in log file to avoid later errors
    def ensure_8_spaces(self, line):
        if not line.startswith(' ' * 8):
            return ' ' * 8 + line.lstrip()
        return line

    # Fixes lines in error message as the outputs from the docker logs can be wildy different
    def fix_error_line(self, line):
        if '\t' in line:
            line = line.replace('\t', '  ')

        if 'TabError:' in line:
            line = '  ' + line

        # Remove any special characters
        if '␛' in line or '␈' in line or '␛' in line or '␛[' in line:
            line = line.replace('␛', '').replace('␈', '').replace('␛', '').replace('␛[', '')

        # Ensure a line is indented correctly
        if 'ETA' in line or '0us/step' in line:
            line = self.ensure_8_spaces(line)

        return line

    # Handles the logging of the error messages and iterations to the log file
    def end_test(self, file_to_open, llm_eval, dockerHelper, error_type, docker_message, loop, run_complete):
        out_file = open(file_to_open, "a")
        python_modules = llm_eval["previous_python_modules"] if 'previous_python_modules' in llm_eval else llm_eval['python_modules']
        out_file.write(f"  iteration_{loop}:\n")
        out_file.write(f'    - python_module: {python_modules}\n')
        out_file.write(f'    - error_type: {error_type}\n')
        out_file.write(f'    - error: |\n')
        if '"stream"' in docker_message:
            error_message = docker_message.replace('{"stream":"', '').replace(':', '')
            docker_message = error_message[:-5]
        previous_line = ''
        extend = ''
        for line in docker_message.split('\n'):
            if not line == '':
            # if not line == '' and not 'errorDetail' in line:
                if '^' in previous_line: extend = '  '  #and not 'iteration' in previous_line else '' # If there's a '^' in the previous line then we need to indent more for formatting
                out_line = f'        {line}\n'
                out_line = self.fix_error_line(out_line)
                out_file.write(f'{extend}{out_line}')
                previous_line = line
        print(loop)
        if loop + 1 > self.end_loop or run_complete:
            end_time = time.time()
            out_file.write(f'end_time: {end_time}\n')
            out_file.write(f'total_time: {end_time - self.start_time}')
            out_file.close()
            dockerHelper.delete_container()
            dockerHelper.delete_image()
            exit(0)
        else:
            return loop + 1

# Handle argument parsing
def process_args():
    parser = argparse.ArgumentParser(description='File to evaluate')
    parser.add_argument('-f', '--file', type=str, help="The full path and name of the file to evaluate")
    parser.add_argument('-b', '--base', type=str, nargs="?", default='http://localhost:11434', const='http://localhost:11434', help="The ollama URL can vary depending on the system")
    parser.add_argument('-m', '--model', type=str, nargs="?", default='phi3:medium', const='phi3:medium', help="The name of the model to use for evaluation")
    parser.add_argument('-t', '--temp', type=str, nargs="?", default='0.7', const='0.7', help="The temperature for the models predictive output. Typically a range from 0-2, default is 0.7")
    parser.add_argument('-l', '--loop', type=int, nargs="?", default=5, const=5, help="How many times we will loop to find a solution")
    parser.add_argument('-r', '--range', type=int, nargs="?", default=0, const=0, help="The search range, expands out above and below the found Python version, defaults to 0")
    parser.add_argument('-i', '--interactive', action="store_true", help="Pause after each iteration and wait for user input")
    parser.add_argument('-v', '--verbose', action="store_true", help="Verbose logging of information")
    return parser.parse_args()

# Main loop
def main():
    llm_eval = None
    llm_details = False
    loop = 0
    
    # Process the arguments, file, model ...
    args = process_args()
    file_path = '/'.join(args.file.split('/')[:-1])

    # Create the main 
    testExecutor = TestExecutor(base_url=args.base, model=args.model, logging=not args.interactive, temp=args.temp, end_loop=args.loop, search_range=args.range, base_modules=file_path+"/modules")
    # Use a simple search to grab imports from file without the LLM
    python_deps = testExecutor.deps.find_word_in_file(args.file, 'import', [])

    # Loop to ensure we handle invalid responses from the model
    while not llm_details:
        try:
            # Evaluate the file to get an initial set of assumptions
            llm_eval = testExecutor.evaluate_file(testExecutor.ollama_helper, args.file)
            
            # Run through all the dependencies and clean them for use. Removes useless imports
            python_deps = testExecutor.pypi.check_module_name(python_deps + llm_eval['python_modules'])

            # Combine the simple search modules with the LLMs suggestions.
            llm_eval['python_modules'] = python_deps

            _say(llm_eval, interactive=args.interactive)
            llm_details = True
        except Exception as e:
            print(f"Failed to get Python modules from file: {e}")
            llm_details = False
            loop += 1
        
        if loop >= 5: break
    # If the LLM didn't return anything, set the Python version to 3.8
    if not llm_details:
        llm_eval = {'python_version': '3.8'}
        llm_eval['python_modules'] = testExecutor.pypi.check_module_name(python_deps)

    # testExecutor.docker_create_process(ollama_helper, llm_eval, args.file, 1)
    # Search range is how far either side of the found Python verion we want to look.
    # For example, a value of 1 where the found version is 3.7 will return [3.6,3.7,3.8]
    python_versions = testExecutor.pypi.get_python_range(python_version=llm_eval['python_version'], pyrange=testExecutor.search_range)
    print(python_versions)
    
    # If python_versions is empty then there was an issue with versions.
    # Give the lowest Python and work with this range
    if not python_versions:
        python_versions = testExecutor.pypi.get_python_range(python_version=llm_eval['python_version'], range=testExecutor.search_range)
    num_processes = (testExecutor.search_range * 2) + 1

    processes = []
    
    # NOTE: CHANGE THIS TO TEST SPECIFIC VERSION
    # python_versions = ['3.8']

    # In interactive mode we keep *one* process only (stdin/stdout in child)
    if args.interactive:
        run_details             = llm_eval.copy()
        run_details['python_version'] = python_versions[0]   # just the first candidate
        testExecutor.docker_create_process(
            OllamaHelper(base_url=args.base, model=args.model, logging=False, temp=args.temp,
                         base_modules=file_path+"/modules"),
            run_details, args.file, 0,  # <‑‑ extra arg “interactive”
            interactive=True)
        return
    
    # In non-interactive mode we run all the processes in parallel
    for i in range(num_processes):
        run_details = llm_eval.copy()
        # Select a version from the python range
        run_details['python_version'] = python_versions[i]
        # run_details['python_version'] = '3.6'
        # Give the docker create process, ollama helper, the snippet analysis, python file and the iteration
        p = mp.Process(target=testExecutor.docker_create_process, args=(OllamaHelper(base_url=args.base, model=args.model, logging=True, temp=args.temp, base_modules=file_path+"/modules"), run_details, args.file, i, False))
        processes.append(p)
        p.start()

    # Wait for all processes to finish
    for p in processes:
        # Give the process 20 minutes to complete
        p.join(timeout=1200)
    
    for p in processes:
        if p.is_alive():
            p.terminate()
        else:
            print("Processing completed without the timeout")

if __name__ == "__main__":
    main()

    print(f"Done")
