"""
This script first erases all the files in a target directory, and then 
copies the necessary files to build the particular component. Afterwards, the .mix 
files in the target directory are ran through the preprocessor.  
The target directory that is passed to the script must exist. It is 
emptied before files are copied over.

It is assumed that you have checked out all the required repos of 
SeattleTestbed into the parent directory of this script.

NOTE WELL: The repositories are used as-is. No attempt is made to switch 
    to a specific branch, pull from remotes, etc.
    (In a future version of this script, the currently active branch 
    for each repo will be displayed as a visual reminder of this fact.)

<Usage>
  build.py  [-t] [-v] [-c] [-r] <target_directory>

    -t or --testfiles copies in all the files required to run the unit tests
    -v or --verbose displays significantly more output on failure to process 
                    a mix file
    -c or --checkapi copies the checkapi source files
    -r or --randomports replaces the default ports of 12345, 12346, and 12347
                        with three random ports between 52000 and 53000. 

<Example>
  Put the Repy runtime and unit test files into a temporary dir, 
  and run the unit tests for module "repyv2api" there.
    user@vm:seattle$ cd dist
    user@vm:dist$ mkdir /tmp/test
    user@vm:dist$ python preparetest.py -t /tmp/test
    user@vm:dist$ cd /tmp/test
    user@vm:test$ python utf.py -m repyv2api

"""

import os
import sys
import glob
import random
import shutil
import optparse
import subprocess


# import testportfiller from path ../repy_v1/tests
sys.path.insert(0, os.path.join(os.path.dirname(os.getcwd()), "repy_v1", "tests"))
import testportfiller
# Remove testportfiller's path again
sys.path = sys.path[1:]



def copy_to_target(file_expr, target):
  """
  This function copies files (in the current directory) that match the 
  expression file_expr to the target folder. 
  The source files are from the current directory.
  The target directory must exist.
  file_expr may contain wildcards (shell globs).
  """
  files_to_copy = glob.glob(file_expr)
  if files_to_copy == []:
    print "WARNING: File expression '" + file_expr + "' does not match any files. Maybe the directory is empty, or the file / directory doesn't exist?"

  for file_path in files_to_copy:
    if os.path.isfile(file_path):
      shutil.copyfile(file_path, target + "/" +os.path.basename(file_path))



def copy_tree_to_target(source, target, ignore=None):
  """
  Copies a directory to the target destination.

  If you pass a string for ignore, then subdirectories that contain the ignore
  string will not be copied over (as well as the files they contain).
  """

  full_source_path = os.path.abspath(source)
  full_target_path = os.path.abspath(target)

  for root, directories, filenames in os.walk(source):
    # Relative path is needed to build the absolute target path.

    # If we leave a leading directory separator in the relative folder
    # path, then attempts to join it will cause the relative folder path
    # to be treated as an absolute path.
    relative_folder_path = os.path.abspath(root)[len(full_source_path):].lstrip(os.sep)

    # If the ignore string is in the relative path, skip this directory.
    if ignore and ignore in relative_folder_path:
      continue

    # Attempts to copy over a file when the containing directories above it do not
    # exist will trigger an exception.
    full_target_subdir_path = os.path.join(full_target_path, relative_folder_path)
    if not os.path.isdir(full_target_subdir_path):
      os.makedirs(full_target_subdir_path)

    for name in filenames:
      relative_path = os.path.join(relative_folder_path, name)
      shutil.copyfile(
        os.path.join(full_source_path, relative_path),
        os.path.join(full_target_path, relative_path))



def process_mix(script_path, verbose):
  """
  Run the .mix files in current directory through the preprocessor.
  script_path specifies the name of the preprocessor script.
  The preprocessor script must be in the working directory.
  """
  mix_files = glob.glob("*.mix")
  error_list = []

  for file_path in mix_files:
    # Generate a .py file for the .mix file specified by file_path
    processed_file_path = (os.path.basename(file_path)).replace(".mix",".py")
    (theout, theerr) =  exec_command(sys.executable + " " + script_path + " " + file_path + " " + processed_file_path)

    # If there was any problem processing the files, then notify the user.
    if theerr:
      print "Unable to process the file: " + file_path
      error_list.append((file_path, theerr))
      
  # If the verbose option is on then print the error.  
  if verbose and len(error_list) > 0:
    print "\n" + '#'*50 + "\nPrinting all the exceptions (verbose option)\n" + '#'*50
    for file_name, error in error_list:
      print "\n" + file_name + ":"
      print error
      print '-'*80



def exec_command(command):
  """
  Execute command on a shell, return a tuple containing the resulting 
  standard output and standard error (as strings).
  """
  # Windows does not like close_fds and we shouldn't need it so...
  process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, 
      stderr=subprocess.PIPE)

  # get the output and close
  theout = process.stdout.read()
  process.stdout.close()

  # get the errput and close
  theerr = process.stderr.read()
  process.stderr.close()

  # FreeBSD prints on stdout, when it gets a signal...
  # I want to look at the last line. It ends in \n, so I use index -2
  if len(theout.split('\n')) > 1 and theout.split('\n')[-2].strip() == 'Terminated':
    # remove the last line
    theout = '\n'.join(theout.split('\n')[:-2])
    
    # However we threw away an extra '\n'. If anything remains, let's replace it
    if theout != '':
      theout = theout + '\n'

  # OS's besides FreeBSD uses stderr
  if theerr.strip() == 'Terminated':
    theerr = ''

  # Windows isn't fond of this either...
  # clean up after the child
  #os.waitpid(p.pid,0)

  return (theout, theerr)



def replace_string(old_string, new_string, file_name_pattern="*"):
  """
  <Purpose>
    Go through all the files in the current folder and replace
    every match of the old string in the file with the new
    string.

  <Arguments>
    old_string - The string we want to replace.
 
    new_string - The new string we want to replace the old string
      with.

    file_name_pattern - The pattern of the file name if you want
      to reduce the number of files we look at. By default the 
      function looks at all files.

  <Exceptions>
    None.

  <Side Effects>
    Many files may get modified.

  <Return>
    None
  """

  for testfile in glob.glob(file_name_pattern):
    # Read in the initial file.
    inFile = file(testfile, 'r')
    filestring = inFile.read()
    inFile.close()

    # Replace any form of the matched old string with
    # the new string.
    filestring = filestring.replace(old_string, new_string)

    # Write the file back.
    outFile = file(testfile, 'w')
    outFile.write(filestring)
    outFile.close()



def help_exit(errMsg, parser):
  """
   Prints the given error message and the help string, then exits
  """
  print errMsg
  parser.print_help()
  sys.exit(1)



def main():
  # Parse the options provided. 
  helpstring = "python preparetest.py [-t] [-v] [-c] [-r] <target>"
  parser = optparse.OptionParser(usage=helpstring)

  parser.add_option("-t", "--testfiles", action="store_true",
      dest="include_tests", default=False,
      help="Include files required to run the unit tests ")
  parser.add_option("-v", "--verbose", action="store_true",
      dest="verbose", default=False,
      help="Show more output on failure to process a .mix file")
  parser.add_option("-c", "--checkapi", action="store_true", 
      dest="copy_checkapi", default=False,
      help="Include checkAPI files")
  parser.add_option("-r", "--randomports", action="store_true", 
      dest="randomports", default=False,
      help="Replace the default ports with random ports between 52000 and 53000. ")

  (options, args) = parser.parse_args()

  # Extract the target directory.
  if len(args) == 0:
    #help_exit("Please pass the target directory as a parameter.", parser)
    target_dir = os.path.join(os.getcwd(),"../build")
    #print os.path.normpath(target_dir)
    #target_dir = os.path.join(target_dir1,"build")
    if not os.path.exists(target_dir):
      os.makedirs(target_dir)
  else:
    target_dir = args[0]
    if not os.path.isdir(target_dir):
      help_exit("Supplied target is not a directory", parser)
  # Make sure they gave us a valid directory
  

  # Set variables according to the provided options.
  repytest = options.include_tests
  RANDOMPORTS = options.randomports
  verbose = options.verbose
  copy_checkapi = options.copy_checkapi


  # This script's parent directory is the root dir of all repositories
  repos_root_dir = os.path.dirname(os.getcwd())

  # Set working directory to the target
  os.chdir(target_dir)	
  files_to_remove = glob.glob("*")

  # Empty the destination
  for entry in files_to_remove: 
    if os.path.isdir(entry):
      shutil.rmtree(entry)
    else:
      os.remove(entry)

  # Create directories for each Repy version under the target
  repy_dir = {"v1" : "repyV1",
      "v2" : "repyV2" }

  for dir_name in repy_dir.values():
    if not os.path.exists(dir_name):
      os.makedirs(dir_name)


  # Return to the repo root
  os.chdir(repos_root_dir)

  
  # Copy the necessary files to the respective target folders:

  lines = [line.rstrip('\n') for line in open('../scripts/config_build.txt')]
  alist = list(line for line in lines if line)
  length = len(alist)
  count =0
  while(count < length):
    repo=alist[count]
    alist0=repo.split(' ', 1)[0]
    if alist0 != "test" and alist0!= "#":
      copy_to_target(alist[count], target_dir)
      count=count + 1
    elif alist0 != "#" and alist0 == "test" and repytest:
      repo=alist[count]
      alist1=repo.split(' ', 1)[1]
      copy_to_target(alist1, target_dir)
      count=count + 1
    else:
      count=count + 1
      continue
    
    
  # Set working directory to the target
  os.chdir(target_dir)

  # Set up dynamic port information
  if RANDOMPORTS:
    print "\n[ Randomports option was chosen ]\n"+'-'*50
    ports_as_ints = random.sample(range(52000, 53000), 5)
    ports_as_strings = []
    for port in ports_as_ints:
      ports_as_strings.append(str(port))
    
    print "Randomly chosen ports: ", ports_as_strings
    testportfiller.replace_ports(ports_as_strings, ports_as_strings)

    # Replace the string <nodemanager_port> with a random port
    random_nodemanager_port = random.randint(53000, 54000)
    print "Chosen random nodemanager port: " + str(random_nodemanager_port)
    print '-'*50 + "\n"
    replace_string("<nodemanager_port>", str(random_nodemanager_port), "*nm*")
    replace_string("<nodemanager_port>", str(random_nodemanager_port), "*securitylayers*")

  else:
    # Otherwise use the default ports...
    testportfiller.replace_ports(['12345','12346','12347', '12348', '12349'], ['12345','12346','12347', '12348', '12349'])

    # Use default port 1224 for the nodemanager port if --random flag is not provided.
    replace_string("<nodemanager_port>", '1224', "*nm*")
    replace_string("<nodemanager_port>", '1224', "*securitylayers*")


  os.chdir("repyV1")
  process_mix("repypp.py", verbose)


  # Change back to root project directory
  os.chdir(repos_root_dir) 



if __name__ == '__main__':
  main()
