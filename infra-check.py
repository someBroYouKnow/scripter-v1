## check torch
import torch
print(torch.__version__, f"torch is available")
## check cuda
print(torch.cuda.is_available(), f"cuda is available with version: ", torch.version.cuda);

## check nemo
import nemo.collections.asr as nemo_asr
print(nemo_asr.__version__, f"nemo is available")