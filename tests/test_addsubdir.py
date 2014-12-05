""" 
test_addsubdir.py --- test if build_component.py can copy files to subdirectories of the build target dir.

""" 
import os 

def main():
	# set component directory
	component_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
	# change directory to component directory ../../common/
	os.chdir(component_dir)

	print '======================= test result ========================='
	
	# open config_build.py and read each lines
	config_file = open("scripts/config_build.txt")
	for line in config_file.readlines():
		# ignore these lines started with "#", '','test'
		if line.startswith('#') or line.strip() == '' or line.startswith('test'):
			continue
		source_spec = line.split()[0]
		try:
			sub_target_dir = line.split()[1]
		except IndexError:
			sub_target_dir = ''
		# delete '*' 
		if source_spec[-1] == '*':
			source_spec = source_spec[ : -1]
		resultdir = os.path.realpath(os.path.join(component_dir, source_spec))		
		target_dir = os.path.realpath(os.path.join(component_dir,'RUNNABLE'+ os.path.sep + sub_target_dir))		
		resultlist = [ f for f in os.listdir(resultdir) if os.path.isfile(os.path.join(resultdir,f)) ]		
		RUNNABLElist = [ f for f in os.listdir(target_dir) if os.path.isfile(os.path.join(target_dir,f)) ]
		# remove .DS_Store file
		if '.DS_Store' in resultlist:
			resultlist.remove('.DS_Store')
		if '.DS_Store' in RUNNABLElist:
			RUNNABLElist.remove('.DS_Store')
		# check if files are copied to target directory
		if RUNNABLElist == resultlist:
			print '{:<50}'.format(sub_target_dir)+'{:>10}'.format('[Pass]')
		else:
			print '{:<50}'.format(sub_target_dir)+'{:>10}'.format('[Fail]')
	
	print '========================== end =============================='

if __name__ == "__main__":
  main()
