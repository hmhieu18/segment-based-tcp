import copy
from PIL import Image, ImageDraw, ImageFont
import os


def visualize_elements(image_path="", output_folder="", save_image=False, customize_name="", nodes=None, index=[], color=None):
    if color is None:
        color = ["red"]*len(nodes)

        for i, node in enumerate(nodes):
            if node.isBlockNode:
                color[i] = "red"
            elif node.isRecordNode:
                color[i] = "green"
    img = Image.open(image_path)
    dr = ImageDraw.Draw(img)

    if nodes is None:
        print("The nodes parameter must be not NoneType!")
        return
    if image_path == "":
        print("The image_path parameter must be not empty string")
        return

    if output_folder == "":
        print("The output_folder parameter must be not empty string")
        return

    for i, node in enumerate(nodes):
        # Initialize rectangle
        if 'bbox' in node.visual_cues:
            bb = node.visual_cues['bbox']
        elif 'bounds' in node.visual_cues:
            bb = node.visual_cues['bounds']
        cor = (bb['x'], bb['y'], bb['x'] +
               bb['width'], bb['y'] + bb['height'])
        line = (cor[0], cor[1], cor[0], cor[3])
        dr.line(line, fill=color[i], width=4)
        line = (cor[0], cor[1], cor[2], cor[1])
        dr.line(line, fill=color[i], width=4)
        line = (cor[0], cor[3], cor[2], cor[3])
        dr.line(line, fill=color[i], width=4)
        line = (cor[2], cor[1], cor[2], cor[3])
        dr.line(line, fill=color[i], width=4)

        # Draw index as number
        index_text = str(index[i]) if i < len(index) else str(i)
        # font = ImageFont.truetype('arial.ttf', 30)
        text_width, text_height = dr.textsize(index_text)
        text_pos = (cor[0], cor[1])
        dr.rectangle((text_pos[0], text_pos[1], text_pos[0] +
                      text_width, text_pos[1] + text_height), fill=color[i])
        dr.text(text_pos, index_text, fill="black")

    if save_image:
        if customize_name == "":
            imagename = image_path.split('/')[-1]
            filename = imagename.split('.png')[0] + '_viz.png'
            save_path = image_path.split(imagename)[0]+filename

            i = 1
            while os.path.exists(save_path):
                save_path = image_path.split(
                    imagename)[0] + imagename.split('.png')[0] + '_viz' + str(i) + '.png'
                i += 1
            img.save(save_path)
        else:
            img.save(output_folder+customize_name)
    else:
        img.show()


# visualize the node and its changing type
'''
    + added: green bounding boxes
    + deleted: red bounding boxes
    + modified: yellow bounding boxes
    + identical: violet bounding boxes
'''


def drawChangingNode(dr, node, allnodes=False):
    if allnodes == False:
        if node is None:
            return
        if node.isBlockNode or node.isRecordNode or True:
            bb = node.visual_cues['bounds']
            color = None
            if node.typeOfChange == 'added':
                color = 'green'
            elif node.typeOfChange == 'deleted':
                color = 'red'
            elif node.typeOfChange == 'identical':
                color = 'gray'
            elif node.typeOfChange == 'modified':
                color = 'yellow'
            elif node.typeOfChange == 'visually_different':
                color = 'violet'
            elif isinstance(node.typeOfChange, list):
                color = 'yellow'
            else:
                # color = 'blue'
                return

            cor = (bb['x'], bb['y'], bb['x'] +
                   bb['width'], bb['y'] + bb['height'])
            line = (cor[0], cor[1], cor[0], cor[3])
            dr.line(line, fill=color, width=4)
            line = (cor[0], cor[1], cor[2], cor[1])
            dr.line(line, fill=color, width=4)
            line = (cor[0], cor[3], cor[2], cor[3])
            dr.line(line, fill=color, width=4)
            line = (cor[2], cor[1], cor[2], cor[3])
            dr.line(line, fill=color, width=4)
            font = ImageFont.truetype("JetBrainsMono-Bold.ttf", 16)
            if node.mapping_id is not None:
                dr.text((bb['x'], bb['y']), str(
                    node.mapping_id), 'black', font=font)

        if node.childNodes:
            for child in node.childNodes:
                drawChangingNode(dr, child)
    else:
        if node is None:
            return

        bb = node.visual_cues['bounds']
        color = None
        if node.typeOfChange == 'added':
            color = 'green'
        elif node.typeOfChange == 'deleted':
            color = 'red'
        elif node.typeOfChange == 'identical':
            color = 'violet'
        elif node.typeOfChange == 'modified':
            color = 'yellow'
        else:
            # color = 'blue'
            return

        cor = (bb['x'], bb['y'], bb['x'] + bb['width'], bb['y'] + bb['height'])
        line = (cor[0], cor[1], cor[0], cor[3])
        dr.line(line, fill=color, width=4)
        line = (cor[0], cor[1], cor[2], cor[1])
        dr.line(line, fill=color, width=4)
        line = (cor[0], cor[3], cor[2], cor[3])
        dr.line(line, fill=color, width=4)
        line = (cor[2], cor[1], cor[2], cor[3])
        dr.line(line, fill=color, width=4)

        if node.childNodes:
            for child in node.childNodes:
                drawChangingNode(dr, child)


def visualize_changes(image_path, output_folder, root_node=None, allnodes=False):
    if root_node is None:
        print("The root_node parameter must be not NoneType!")
        return
    if image_path == "":
        print("The image_path parameter must be not empty string")
        return
    if output_folder == "":
        print("The output_folder parameter must be not empty string")
        return

    img = Image.open(image_path)
    draw = ImageDraw.Draw(img)
    drawChangingNode(draw, root_node, allnodes)
    img.save(output_folder+'visualize_changes.png')


def visualize_on_segmentation(dom):   
    img = Image.open(dom.imgOut)
    width, height = img.size
    tmp_img = Image.new("RGBA", (width, height))
    draw = ImageDraw.Draw(tmp_img)
    
    opacity = 128

    #copy final_segments to viz_nodes
    viz_nodes = copy.copy(dom.final_segments)

    viz_rectangles = {
        'identical': [],
        'visually_different': [],
        'modified': [],
        'added': [],
        'deleted': []
    }
    viz_rects = [] # list of tuples (rectangle, color, level)

    colors = {
        'added': (0, 128, 255, opacity),
        'deleted': (255, 0, 0, opacity),
        'modified': (255, 255, 0, opacity),
        'identical': (0, 255, 0, opacity),
        'visually_different': (255, 0, 255, opacity)
    }

    for node in viz_nodes:
        bb = None
        if 'bbox' in node.visual_cues:
            bb = node.visual_cues['bbox']
        elif 'bounds' in node.visual_cues:
            bb = node.visual_cues['bounds']
        if bb is None:
            continue

        fill_color = None
        if node.typeOfChange == "added":
            # fill_color = (0, 128, 255, opacity)
            viz_rectangles['added'].append(bb)
            viz_rects.append((bb, colors['added'], node.level))
        elif node.typeOfChange == "deleted":
            fill_color = (255, 0, 0, opacity)
            viz_rectangles['deleted'].append(bb)
            viz_rects.append((bb, colors['deleted'], node.level))
        elif node.typeOfChange == "identical":
            fill_color = (0, 255, 0, opacity)
            viz_rectangles['identical'].append(bb)
            viz_rects.append((bb, colors['identical'], node.level))
        elif node.typeOfChange == "visually_different":
            fill_color = (255, 0, 255, opacity)
            viz_rectangles['visually_different'].append(bb)
            viz_rects.append((bb, colors['visually_different'], node.level))
        elif isinstance(node.typeOfChange, list):
            if len(node.typeOfChange) > 0:
                fill_color = (255, 128, 0, opacity)
                viz_rectangles['modified'].append(bb)
                viz_rects.append((bb, colors['modified'], node.level))
            else:
                fill_color = (0, 255, 0, opacity)
                viz_rectangles['identical'].append(bb)
                viz_rects.append((bb, colors['identical'], node.level))
        
        for child in node.childNodes:
            viz_nodes.append(child)

    # for key in viz_rectangles:
    #     for bb in viz_rectangles[key]:
    #         draw.rectangle([(int(bb['x']), int(bb['y'])), (int(bb['x']+bb['width']), int(bb['y']+bb['height']))], fill=colors[key])

    #sort the rectangles by level 
    viz_rects.sort(key=lambda tup: tup[2])
    for rect in viz_rects:
        draw.rectangle([(int(rect[0]['x']), int(rect[0]['y'])), (int(rect[0]['x']+rect[0]['width']), int(rect[0]['y']+rect[0]['height']))], fill=rect[1])

    img = Image.alpha_composite(img.convert("RGBA"), tmp_img)
    img.save(dom.base_dir+"segment_comparison.png")

def visualize_identical(dom, nodes):
    img = Image.open(dom.imgOut)
    width, height = img.size
    tmp_img = Image.new("RGBA", (width, height))
    draw = ImageDraw.Draw(tmp_img)
    
    opacity = 128

    for segment in nodes:
        bb = None
        if 'bbox' in segment.visual_cues:
            bb = segment.visual_cues['bbox']
        elif 'bounds' in segment.visual_cues:
            bb = segment.visual_cues['bounds']
        if bb is None:
            continue

        fill_color = (138, 43, 226, opacity)
        draw.rectangle([(int(bb['x']), int(bb['y'])), (int(bb['x']+bb['width']), int(bb['y']+bb['height']))], fill=fill_color)

    img = Image.alpha_composite(img.convert("RGBA"), tmp_img)
    img.save(dom.base_dir+"identical.png") 