help = r"""
# User Guide

## 0. Service Configuration and Usage
#### This project can call 2 local projects: Bert-VITS2, GPT-SoVITS
#### And 1 online service: Microsoft TTS
* **For Local TTS Projects**:

    * Fill in and save the project root path and the corresponding python interpreter path in the settings page.
    * **A Simpler method**: Place the program in the root directory of the integrated package, then click the corresponding button on the first page to start the API service!

* **For Microsoft TTS**:

    * Follow the tutorial to register an account and fill in the API key on the settings page.
    * Note the monthly free quota!

## 1. Getting Started
### This project supports dubbing for subtitles or plain text.
* **For subtitles**:

    * When a subtitle is too long, subsequent subtitles will be delayed accordingly.And you can set the minimum speech interval in settings.

* **For plain text**:

    * The text will be split into subtitle entries based on ending punctuation and line breaks.

* After generation, you can export subtitles with actual audio timestamps in the editing page.

### A. Single Speaker Scenario
* **I.** Upload subtitle or text files in the right panel of the `Subtitle Dubbing` page.

* **II.** Select your project and adjust parameters in the middle panel.

* **III.** Click `Generate Audio` Button at the bottom and wait.

* **IV.** Download your audio.

### B. Multi-Speaker Scenario
* **I.** Upload subtitle/text files in the right panel of `Subtitle Dubbing`. 
* Marking mode: The content of the file should be as follows: `Speaker:Content`, e.g. `Jerry: Hello.` The mapping table can convert the original speaker in the text file into the corresponding target speaker.  

* **II.** Click `Create Multi-Speaker Dubbing Project` below the file display.

* **III.** Create speakers:
    * **a.** Expand the Multi-Speaker Dubbing section at the bottom of the editing page.
    * **b.** Select the target project.
    * **c.** In the Select/Create Speaker box, enter a speaker name.
    * **d.** Adjust parameters (including port numbers) and click 💾 to save. Duplicate names will overwrite existing speakers.

* **IV.** Select a speaker from the dropdown, check corresponding subtitles, then click ✅ to apply. Speaker info will appear in Column 4.

* **V.** The last assigned speaker becomes the default speaker (applies to unassigned subtitles in multi-speaker projects).

* **VI.** Click Generate Multi-Speaker Dubbing to start generation.

### Regenerating Specific Lines
* **I.** Locate the target subtitle using the slider in the editing page.

* **II.** Modify the text if needed. Changes are auto-saved after regeneration.

* **III.** Click 🔄 to regenerate a single line:

    * Uses project parameters if unassigned.
    * Uses speaker-specific parameters if assigned.
    * Multi-speaker projects must have assigned speakers.

* **IV.** After making changes to the subtitles, you can also click `Continue Generation` to regenerate the audios of the changed subtitles or those that failed to be synthesized.

* **V.** Click `Reassemble Audio` to recompose full audio.

### C. Re-editing Historical Projects
* Select a project from the synthesis history in the top panel. Then click `Load` button.
* The rest is self-explanatory.

### D. Subtitle Editing
#### 1. Copy
* Copy selected subtitles.

#### 2. Delete
* Delete selected subtitles.

#### 3. Merge
* Select no less than 2 subtitles as start/end points.
* Subtitles from the starting point to the ending point will be merged.

⚠️ Changes aren't auto-saved to drive immediately, therefore you can reload the project to undo.

#### 4. Modify Timestamps
* Edit start/end times in SRT format.
* Click `Apply Timestamps` to save changes.

⚠️ Unapplied changes will be lost during navigation.

## 2. Troubleshooting
* When reporting issues:  
Describe the problem in detail and list steps taken before the error occurred.
* Go to [GitHub-issues](https://github.com/YYuX-1145/Srt-AI-Voice-Assistant/issues) to report a problem or ask for help (Issue templates will guide proper reporting).
"""
