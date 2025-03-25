help_custom = r"""
## 安全警告：此功能会执行外部代码！  
### 运行前请务必检查代码内容，运行不受信任的代码可能会导致电脑受到攻击！  
### 作者不对此产生的后果负任何责任！！

### 将装有python函数的代码文件放在`SAVAdata/presets`下即可被调用  
```
def custom_api(text):#return: audio content
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
以上是接入Gradio的一个示例代码，请注意：函数的输入值必须是要合成的文本`text`,返回值是音频文件的二进制内容！

"""
