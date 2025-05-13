issues = r"""
# Typical Issues
## 1. GPT-SoVITS Error: 404 NOT FOUND
```
/tts 404 NOT FOUND
```
* Typical cause of this error: Using non-official standard code  
* Please ensure that you are using the official integrated package or the latest code from the official repository. 

### Solution:
* Manually pull the official repository code.
* Download the integrated package provided in README. (stable but updates may be slow)

## 2. No connection could be made because the target machine actively refused it.
```
No connection could be made because the target machine actively refused it.
```
You need to check:  
* Is the API service already started and running?
* Please wait for the API to fully start before performing operations.
* Do not close the API console!  
* Is the port correctly filled?

## 3. 400 Bad Request
```
400 Bad Request
```
Check the red error logs in this program's console; usually, the API will return the cause of the error.  
If no error message is received, please report this issue.
* Typical error cause: Reference audio outside the 3-10 second range; model path does not exist;

## 4. The following subtitles are delayed due to the previous audio being too long.
```
The following subtitles are delayed due to the previous audio being too long.
```
* Your subtitle timing intervals are not proper.
* Consider increasing the value of the setting `Maximum audio acceleration ratio` (setting it to a value greater than 1 to enable the feature) and enable `Remove inhalation and silence`.  
* There is a minimum voice interval option in the settings (default 0.3 seconds) to prevent voices from overlapping in such cases. If not needed, it can be set to 0.

## 5. GPT-SoVITS Output Audio Has Duration But It's Silent
```
GPT-SoVITS Output Audio Has Duration But It's Silent
```
* Your GPU does not support fp-16.
* Manually modify the value of `is_half` to `false` in `GPT_SoVITS\configs\tts_infer.yaml`.
"""
