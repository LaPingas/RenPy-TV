# RenPy-TV

A WIP RenPy visual-novel that uses TV channels as the source material.

# How to run
Download and run the [RenPy SDK](https://www.renpy.org/latest.html).
Launch the TV channel chunk retreiving server using
```bash
python extract_data.py
```
Then launch the RenPyTV project from the RenPy SDK.

# TODO
- Better subs detection
- Implement some code blocks more efficiently
- Reverse subs based on language + move reverse to server
- Multiclient handling? Currently every user runs both processes, could be a waste to not share resources
- Add cool manipulations
- Channel selection
