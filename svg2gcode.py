#!/usr/bin/env python

import sys
import xml.etree.ElementTree as ET
import shapes as shapes_pkg
from shapes import point_generator
from config import *
import re

path = "./example.svg"
output = "./gcode/output1.gcode"
debug = False

# todo add manual scale option
# todo add z rise option

def generate_gcode(path, autoScale = True):
    svg_shapes = set(['rect', 'circle', 'ellipse', 'line', 'polyline', 'polygon', 'path'])

    with open("header.txt") as headerFile:
        header = headerFile.read()

    commands = []
    tree = ET.parse(path)
    root = tree.getroot()
    width = root.get('width')
    height = root.get('height')

    if width == None or height == None:
        viewbox = root.get('viewBox')
        if viewbox:
            _, _, width, height = viewbox.split()

    if width == None or height == None:
        print("Unable to get width and height for the svg")
        sys.exit(1)

    width = float(re.sub("[^0-9]", "", width))
    height = float(re.sub("[^0-9]", "", height))
    print("\n width / height")
    print(width, height)

    if autoScale:

        scale_x = min(bed_max_x / max(width, height),bed_max_y / max(width, height))
        scale_y = scale_x

    else:

        scale_x = 1
        scale_y = 1

    print("scale factor: ", scale_y)

    if debug:
        print("\n preamble")
        print(preamble)

    commands.append(header)
    commands.append("(begintintin)")
    commands.append(preamble)
    commands.append(f"F{feed_rate}")

    print("\n begin main loop")

    for elem in root.iter():

        if debug:
            print("\n\n\n***************** elem ******************")
            print(elem)

        try:
            _, tag_suffix = elem.tag.split('}')

        except ValueError:
            continue

        if tag_suffix in svg_shapes:

            if debug:
                print("\n tag_suffix")
                print(tag_suffix)

            for i in ["\n", "({})".format(tag_suffix), ""]:
                commands.append(i)  # add tag name ad comment

            shape_class = getattr(shapes_pkg, tag_suffix)
            if debug:
                print("\n shape_class")
                print(shape_class)

            shape_obj = shape_class(elem)
            if debug:
                print("\n shape_obj")
            #print(shape_obj)

            d = shape_obj.d_path()

            m = shape_obj.transformation_matrix()  # todo work out what d and m are

            if debug:
                print("\n d", d)
                print(d)
                print("\n m", m)
                print(m)

            if d:  # begin shape processing
                if debug:
                    print("\n shape preamble")
                    print(shape_preamble)

                commands.append(shape_preamble)

                p = point_generator(d, m, smoothness)  # tuples of x y coords

                first = True
                for x, y in p:

                    if first:

                        command = g_string(x * scale_x, (-y+height)  * scale_y, zTravel, "G0", precision) #todo why do i need to flip?
                        commands.append(command)
                        if debug:
                            print(command)
                        first = False

                    # if x > 0 and x < bed_max_x and y > 0 and y < bed_max_y:

                    command = g_string(x * scale_x, (-y+height) * scale_y, zDraw, "G1", precision)
                    commands.append(command)
                    if debug:
                        print(command)

                command = g_string(x, y, zTravel, "G0", precision)
                commands.append(command)

                if debug:
                    print(shape_postamble)
                commands.append(shape_postamble)

    print(postamble)
    commands.append(postamble)
    return commands


def g_string(x, y, z=False, prefix="G1", p=3):
    if z is not False:
        return f"{prefix} X{x:.{p}f} Y{y:.{p}f} Z{z:.{p}f}"

    else:
        return f"{prefix} X{x:.{p}f} Y{y:.{p}f}"


if __name__ == "__main__":
    c = generate_gcode(path)


    with open(output, 'w+') as output_file:
        for i in c:
            output_file.write(i + "\n")

    print("done")
