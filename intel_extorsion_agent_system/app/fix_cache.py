import time
import shutil
import os
from fastembed import TextEmbedding

success = False
for i in range(5):
    try:
        print(f'Attempt {i+1} to download model...')
        TextEmbedding('sentence-transformers/all-MiniLM-L6-v2')
        success = True
        print('Successfully downloaded and loaded model!')
        break
    except Exception as e:
        print(f'Failed: {e}')
        if os.path.exists('/tmp/fastembed_cache/'):
            shutil.rmtree('/tmp/fastembed_cache/')
        time.sleep(2)

if not success:
    exit(1)
