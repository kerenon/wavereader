# WaveReader
Create audiobook albums from epub files using Googles WaveNet voices

# Warning
In its current form, this is nothing more than a proof-of-concept that I hacked together, to see if it's even possible. It is BTW :).
For now, if you can get it to work, it breaks the epub file into chapters, and creates neat little albums in flac format.

# The good, the bad and the epub
During development, I realized that either the epub format is waaaay too forgiving, or the epub files found in the wild simply
don't give a rat's ass about sticking to the format specifications. The end result is that parsing epub files is a clusterfuck.
It seems none of the python epub libraries (that I know of) could parse the ~20 epubs in my test package the way I want/need it. I could just treat them
az zip files and parse the xml myself, but I'm not really sure want to do that. I'll probably gonna take a look at other language/library pairs,
and choose on that I like, and that can handle all my test files.

One of the last test-runs produced something like this:

```
Arifureta - Volume 3_01_Prologue.opus
Arifureta - Volume 3_02_Chapter I An Adventurer's Job.opus
Arifureta - Volume 3_03_Chapter II A New Meeting.opus
Arifureta - Volume 3_04_Chapter III The Sack of Ur.opus
Arifureta - Volume 3_05_Epilogue I.opus
Arifureta - Volume 3_06_Epilogue II.opus
Arifureta - Volume 3_07_Extra Chapter A Very Dramatic Before and After.opus
Arifureta - Volume 3_08_Afterword.opus
Arifureta - Volume 3_09_Bonus Short Stories.opus
Arifureta - Volume 3_10_About J-Novel Club.opus
Arifureta - Volume 3_11_Copyright.opus
```

The files are not (yet) tagged, no cover art, no playlist, no nothing. Like I said, it barely works.

# Credits
Original idea [Ollin Boer Bohan](https://gist.github.com/madebyollin), Code snippets from [make_audiobook.py](https://gist.github.com/madebyollin/508930c86fa12e1a70e32d91411485a8)
