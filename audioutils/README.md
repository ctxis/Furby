# Audio Utils

**WARNING**: These scripts are very rough. You'll need to customise the file/directory names to make them work. 

You'll also need to download the [GeneralPlus Gadget utility](http://www.generalplus.com/1LVlangLNxxSVyySNservice_n_support_d) and extract the a1800.dll file from it. 

 - ```extract_audio.py``` - extracts the GeneralPlus a18-encoded audio files from the DLC file
 - ```convert.py``` - converts a directory of a18 files to wav, using Python's ctypes to call into the a1800 DLL. You'll need to run this on Windows.