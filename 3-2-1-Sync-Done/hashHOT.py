import hashlib
import logging #Needed for proper error handling.
import time
#hash256 method generates the SHA256 for my program.
logging.basicConfig(level=logging.WARNING, filename='loginfo.log', format='%(asctime)s - %(levelname)s: %(message)s')
def hash256_caller(file, attempt = 3):
   for i in range(attempt):
        result = hash256(file)
        if result:
            return result
        time.sleep(1) 
        logging.warning(f"Retry {i+1} for {file}")
   return None

def hash256(file, max = 65536): #This is needed 
    #because without the max size, then it would take too much ram
    #since each of the files would be loaded there, and I don't want that 
    #for the program
    sha256 = hashlib.sha256()
    try:
        with open(file, 'rb') as f:
              while True:
                read_file = f.read(max)
                if not read_file:
                      break
                sha256.update(read_file)
        return sha256.hexdigest() #The hex of the hash.
    #The following exceptions are like C's perror which is interesting.
    except PermissionError:
       logging.error(f"Permission denied: {file}")
    except FileNotFoundError:
        logging.error(f"File not found: {file}")
    except Exception as e:
        logging.error(f"Unexpected error processing {file}: {e}")
    return None 
#Logging to file:
#https://docs.python.org/3/howto/logging.html