help_custom = r"""
## Security Warning: This feature will execute external code!
### Please inspect the code content before running it; executing untrusted code may put your computer at risk!
### The author bear no responsibility for any consequences!

### Place code files containing Python functions in the SAVAdata/presets directory, and they will be callable.
* Here is an example code for Gradio API.
```
def custom_api(text): #return: audio content
    from gradio_client import Client
    client = Client("http://127.0.0.1:7860/")
    result = client.predict(
		text,	# str  in '输入文本内容' Textbox component
		"神里绫华",	# str (Option from: [('神里绫华', '神里绫华')]) in 'Speaker' Dropdown component
		0.1,	# int | float (numeric value between 0 and 1) in 'SDP Ratio' Slider component
		0.5,	# int | float (numeric value between 0.1 and 2) in 'Noise' Slider component
		0.5,	# int | float (numeric value between 0.1 and 2) in 'Noise_W' Slider component
		1,	# int | float (numeric value between 0.1 and 2) in 'Length' Slider component
		"auto",	# str (Option from: [('ZH', 'ZH'), ('JP', 'JP'), ('EN', 'EN'), ('mix', 'mix'), ('auto', 'auto')]) in 'Language' Dropdown component
		"",	# str (filepath on your computer (or URL) of file) in 'Audio prompt' Audio component
		"",	# str  in 'Text prompt' Textbox component
		"",	# str  in 'Prompt Mode' Radio component
		"",	# str  in '辅助文本' Textbox component
		0,	# int | float (numeric value between 0 and 1) in 'Weight' Slider component
		fn_index=0
    )
    with open(result[1],'rb') as file:
        data=file.read()
    return data
```
**Please note: The input value `text` of the function must be the text to be synthesized, and the return value is the binary content of the audio file!**
"""
