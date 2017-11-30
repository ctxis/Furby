# Furby
## Python tools for handing Furby Connect DLC files

<p align="center">
	<img src="images/gifs/gif-full-padding-100.gif">
</p>

**Disclaimer: This script is pretty alpha; use at your own risk. Bad DLCs can make your Furby Connect very unhappy.**

### The original blog post can be found [here](https://www.contextis.com/blog/dont-feed-them-after-midnight-reverse-engineering-the-furby-connect)


## DLC Class

This class is a wrapper around the syntax used by Furby Connect DLC files. To use it, add the line `from furby import dlc` to the top of your script:

```
#!/usr/bin/env python
# -*- coding: utf-8 -*-

from furby import dlc

def main():
    ...
    <your python here>
    ...
```

The class can be instantiated with an existing Furby Connect DLC by passing the path to one such DLC when creating an instance of the class:

```
D = dlc("./dlc/dlc1/tu012700.dlc")
```

You can then access each of the various sections contained in the DLC via the `dlc_sections` dictionary:

```
cels_section = D.dlc_sections["XLS"]
```

Each of the sections has a "main" storage object, which is either a list or a dictionary as appropriate to the section. Notable main storage objects are as follows:

```
xls_tree             = D.dlc_sections["XLS"].action_tree
colour_palettes      = D.dlc_sections["PAL"].palettes
eye_sprites          = D.dlc_sections["CEL"].cels
animation_scheduling = D.dlc_sections["SPR"].anim_tree
audio_samples        = D.dlc_sections["AMF"].tracks
audio_playlists      = D.dlc_sections["APL"].playlists
lip_movements        = D.dlc_sections["LPS"].phrases
response_scheduling  = D.dlc_sections["SEQ"].sequences
servo_movements      = D.dlc_sections["MTR"].animations
```

For more information on what each section does and how they relate to one another, [check out our writeup](https://www.contextis.com/blog/dont-feed-them-after-midnight-reverse-engineering-the-furby-connect), which covers it in a fair amount of detail.

After making modifications to a DLC, you can build it back into a new DLC by calling the `build()` function, passing the path to the output file:

```
D.build("/tmp/new_dlc.dlc")
```



## Helper Functions

Modifying a DLC can be achieved by changing the content stored in each part of the dlc sections, but we have also included a number of helper functions to make common tasks more straightforward.


### extract_palette()

`D.dlc_sections["PAL"].extract_palette()` will, if passed a .gif with a (single) 64-colour palette, extract that palette and convert it into the same format used as internal storage by the dlc class. This means you can do things like this:

```
# extract the palette from a gif
new_palette = D.dlc_sections["PAL"].extract_palette("./my_gif.gif")

# replace the nth palette in the DLC with this new palette
n = 5
D.dlc_sections["PAL"].palettes[n] = new_palette
```

### quarterize()

`D.dlc_sections["CEL"].quarterize()` will, if passed a 128x128 pixel .gif, convert that gif into a sequence of quarter-frames, in the same form as that used by the dlc class' internal storage. This means that you can do things like this:

```
# quarterize a gif
new_cels = D.dlc_sections["CEL"].quarterize("./my_gif.gif")

# replace the nth cel in the DLC with the mth of our new cels
n = 5
m = 3
D.dlc_sections["CEL"].cels[n] = new_cels[m]

# To view the quarters as they get made, just pass in a palette to render them with.
new_palette = D.dlc_sections["PAL"].extract_palette("./my_gif.gif")
new_cels = D.dlc_sections["CEL"].quarterize("./my_gif.gif", new_palette)
```

### replace_track()

`D.dlc_sections["AMF"].insert_track()` will replace one of the tracks in the AMF section with a track supplied by you. It can be used in the following way:

```
# Replace the nth audio track.
n = 9
D.dlc_sections["AMF"].replace_track(n, "mytrack.a18")
```

### minify_audio()

`D.dlc_sections["AMF"].minify_audio()` will shrink all the audio files in a DLC to a given length. This is useful if you're going to be testing multiple DLC files, as it will drastically shrink the size of your DLCs, resulting in faster uploads. You can use it like so:

```
# Shrink a DLC
D = dlc("./dlc/dlc1/tu012700.dlc")
D.dlc_sections["AMF"].minify_audio()
D.build("/tmp/minified_dlc.dlc")
```

### dump_images()

`D.dump_images()` will attempt to render and output all the cels it finds in the DLC. It also needs to be passed the index to the palette it'll use to render each image. Here's an example snippet:

```
# Draw chillis.
D = dlc("./dlc/dlc1/tu003140.dlc")
D.dump_images(4)
```

## Contributing

We really hope you enjoy tinkering with the scripts. If you'd like to contribute, here are a few things that still need work:

 - Cataloguing the motions in the MTR section
 - Improving the `__compile__()` function of both the XLS and SPR sections to be more robust
 - Implementing an analogue of the GeneralPlus a18 codec in Python, for converting .wav file

Enjoy - we're looking forward to seeing what you make with it!
