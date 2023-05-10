#Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

"""Generate images using pretrained network pickle."""
import pickle
from website import app, auth, db, storage
from PIL import Image, ImageDraw, ImageFont
import operator
import cv2
import random
from flask import session

import os
import re
from typing import List, Optional

import click
import dnnlib
import numpy as np
import PIL.Image
import torch

import legacy as legacy

import sys
sys.path.append("C:/xampp/htdocs/LoGo/Lo-Go_Logo-on-the-go/web app/website")

#----------------------------------------------------------------------------

def randseed():
    return random.randint(0, 10000)

seed1 = randseed()
seed2 = randseed()

def num_range(s: str) -> List[int]:
    '''Accept either a comma separated list of numbers 'a,b,c' or a range 'a-c' and return as a list of ints.'''

    range_re = re.compile(r'^(\d+)-(\d+)$')
    m = range_re.match(s)
    if m:
        return list(range(int(m.group(1)), int(m.group(2))+1))
    vals = s.split(',')
    return [int(x) for x in vals]

#----------------------------------------------------------------------------
@click.command()
@click.pass_context
@click.option('--user', 'user_id', default=auth.get_account_info(session['user'])['users'][0]['localId'], show_default=True)
@click.option('-i', 'input',nargs=4, type=click.STRING, default=[session['name'], session['slogan'], session['style'], session['color']])
@click.option('--network', 'network_pkl', help='Network pickle filename', default="C:/xampp/htdocs/LoGo/Lo-Go_Logo-on-the-go/web app/website/generator/network.pkl", show_default=True)
@click.option('--seeds', type=num_range, help='List of random seeds', default=f"{seed1},{seed2}", show_default=True)
@click.option('--trunc', 'truncation_psi', type=float, help='Truncation psi', default=1, show_default=True)
@click.option('--class', 'class_idx', type=int, help='Class label (unconditional if not specified)')
@click.option('--label', 'raw_label', type=num_range, help='Raw label', default=f"{session['gender']},{session['class']},{session['age']},{session['domain']},{session['subdomain']}")
@click.option('--noise-mode', help='Noise mode', type=click.Choice(['const', 'random', 'none']), default='random', show_default=True)
@click.option('--projected-w', help='Projection result file', type=str, metavar='FILE')
@click.option('--outdir', help='Where to save the output images', type=str, default="web app/website/static/assets/img/generated logos", show_default=True, metavar='DIR')
def generate_images(
    ctx: click.Context,
    network_pkl: str,
    user_id: str,
    input: Optional[List[str]],
    seeds: Optional[List[int]],
    truncation_psi: float,
    noise_mode: str,
    outdir: str,
    class_idx: Optional[int],
    raw_label: Optional[List[int]],
    projected_w: Optional[str]
):

    print('Loading networks from "%s"...' % network_pkl)
    device = torch.device('cuda')
    with dnnlib.util.open_url(network_pkl) as f:
        G = legacy.load_network_pkl(f)['G_ema'].to(device) # type: ignore

    os.makedirs(outdir, exist_ok=True)

    # Synthesize the result of a W projection.
    if projected_w is not None:
        if seeds is not None:
            print ('warn: --seeds is ignored when using --projected-w')
        print(f'Generating images from projected W "{projected_w}"')
        ws = np.load(projected_w)['w']
        ws = torch.tensor(ws, device=device) # pylint: disable=not-callable
        assert ws.shape[1:] == (G.num_ws, G.w_dim)
        for idx, w in enumerate(ws):
            img = G.synthesis(w.unsqueeze(0), noise_mode=noise_mode)
            img = (img.permute(0, 2, 3, 1) * 127.5 + 128).clamp(0, 255).to(torch.uint8)
            img = PIL.Image.fromarray(img[0].cpu().numpy(), 'RGB').save(f'{outdir}/proj{idx:02d}.png')
        return

    if seeds is None:
        ctx.fail('--seeds option is required when not using --projected-w')

    # Labels.
    label = torch.zeros([1, G.c_dim], device=device)
    if G.c_dim != 0:
        if class_idx is None and raw_label is None:
            ctx.fail('Must specify class label with --class or --label when using a conditional network')
        if class_idx is not None:
            label[:, class_idx] = 1
        if raw_label is not None:
            label = torch.unsqueeze(torch.tensor(raw_label,device=device),0)
    else:
        if class_idx is not None:
            print ('warn: --class=lbl ignored when running on an unconditional network')

    # Generate images.
    for seed_idx, seed in enumerate(seeds):
        print('Generating image for seed %d (%d/%d) ...' % (seed, seed_idx, len(seeds)))
        z = torch.from_numpy(np.random.RandomState(seed).randn(1, G.z_dim)).to(device)
        img = G(z, label, truncation_psi=truncation_psi, noise_mode=noise_mode)
        img = (img.permute(0, 2, 3, 1) * 127.5 + 128).clamp(0, 255).to(torch.uint8)
        PIL.Image.fromarray(img[0].cpu().numpy(), 'RGB').save(f'{outdir}/seed{seed:04d}.png')

    print("GENERATING TEXT COMPONENT...")
    
    def create_image(size, bgColor, name,slogan,sloganFont, font, position):
        W, H = size
        image = Image.new('RGB', size, bgColor)
        draw = ImageDraw.Draw(image)
        _, _, w, h = draw.textbbox((0, 0), name, font=font)
        _, _, w2, h2 = draw.textbbox((0, 0), slogan, font=sloganFont)
        if position == 'down':
            draw.text(((W-max(w,w2))/2, (H/2+135)), name, font=font, fill='blue')
            draw.text(((W-max(w,w2))/2, (H/2+135+h)), slogan, font=sloganFont, fill='green')
        elif position == 'up':
            draw.text(((W-max(w,w2))/2, (H-(h+h2))/2-h2-145), name, font=font, fill='blue')
            draw.text(((W-max(w,w2))/2, (H-(h+h2))/2-135), slogan, font=sloganFont, fill='green')
        elif position == 'left':
            draw.text(((W/2-w-135), (H-(h+h2))/2), name, font=font, fill='blue')
            draw.text(((W/2-w2-135), (H+h)/2), slogan, font=sloganFont, fill= 'green')
        else:
            draw.text(((W/2+135), (H-(h+h2))/2), name, font=font, fill='blue')
            draw.text(((W/2+135), (H+h2)/2), slogan, font=sloganFont, fill='green')

        return image

    name = input[0]
    slogan = input[1]
    font = input[2]
    color = input[3]

    nameFont = ImageFont.truetype('C:/xampp/htdocs/LoGo/Lo-Go_Logo-on-the-go/web app/fonts/'+font+'.ttf', 40)
    sloganFont = ImageFont.truetype('C:/xampp/htdocs/LoGo/Lo-Go_Logo-on-the-go/web app/fonts/'+font+'.ttf', 30)
    
    img = create_image((800,800),'white',name,slogan,sloganFont,nameFont,"down")
    im2 = Image.open(f'{outdir}/seed{seed1}.png')
    img.paste(im2,[int(400-im2.size[0]/2),int(400-im2.size[1]/2)])

    img = img.convert('L')

    gray = np.array(img) 
    image = cv2.cvtColor(gray,cv2.COLOR_GRAY2RGB)
    image =Image.fromarray(image)
    
    width, height = image.size

    for x in range(height):
        for y in range(width):
            if image.getpixel((x,y)) != (255,255,255):
                if color=='blue':
                    image.putpixel( (x, y), tuple(map(operator.add, image.getpixel((x,y)), (0,50,150))) )
                elif color=='red':
                    image.putpixel( (x, y), tuple(map(operator.add, image.getpixel((x,y)), (150,0,0))) )
                elif color=='green':
                    image.putpixel( (x, y), tuple(map(operator.add, image.getpixel((x,y)), (0,100,0))) )
                elif color=='black':
                    image.putpixel( (x, y), tuple(map(operator.add, image.getpixel((x,y)), (0,0,0))) )
                elif color=='grey':
                    image.putpixel( (x, y), tuple(map(operator.add, image.getpixel((x,y)), (80,80,80))) )
                elif color=='brown':
                    image.putpixel( (x, y), tuple(map(operator.add, image.getpixel((x,y)), (80,40,20))) )
                elif color=='yellow':
                    image.putpixel( (x, y), tuple(map(operator.add, image.getpixel((x,y)), (150,120,0))) )
                elif color=='pink':
                    image.putpixel( (x, y), tuple(map(operator.add, image.getpixel((x,y)), (200,0,100))) )
                elif color=='orange':
                    image.putpixel( (x, y), tuple(map(operator.add, image.getpixel((x,y)), (200,80,0))) )
                elif color=='purple':
                    image.putpixel( (x, y), tuple(map(operator.add, image.getpixel((x,y)), (80,0,120))) )
                
    image.save(f'{outdir}/seed{seed1}.png')
    storage.child(f"logo/{user_id}/firstlogo.png").put(f'{outdir}/seed{seed1}.png')

    print('FIRST LOGO DONE')

    img = create_image((800,800),'white',name,slogan,sloganFont,nameFont,"right")
    im2 = Image.open(f'{outdir}/seed{seed2}.png')
    img.paste(im2,[int(400-im2.size[0]/2),int(400-im2.size[1]/2)])

    img = img.convert('L')

    gray = np.array(img) 
    image = cv2.cvtColor(gray,cv2.COLOR_GRAY2RGB)
    image =Image.fromarray(image)
    
    width, height = image.size

    for x in range(height):
        for y in range(width):
            if image.getpixel((x,y)) != (255,255,255):
                if color=='blue':
                    image.putpixel( (x, y), tuple(map(operator.add, image.getpixel((x,y)), (0,50,150))) )
                elif color=='red':
                    image.putpixel( (x, y), tuple(map(operator.add, image.getpixel((x,y)), (150,0,0))) )
                elif color=='green':
                    image.putpixel( (x, y), tuple(map(operator.add, image.getpixel((x,y)), (0,100,0))) )
                elif color=='black':
                    image.putpixel( (x, y), tuple(map(operator.add, image.getpixel((x,y)), (0,0,0))) )
                elif color=='grey':
                    image.putpixel( (x, y), tuple(map(operator.add, image.getpixel((x,y)), (80,80,80))) )
                elif color=='brown':
                    image.putpixel( (x, y), tuple(map(operator.add, image.getpixel((x,y)), (80,40,20))) )
                elif color=='yellow':
                    image.putpixel( (x, y), tuple(map(operator.add, image.getpixel((x,y)), (150,120,0))) )
                elif color=='pink':
                    image.putpixel( (x, y), tuple(map(operator.add, image.getpixel((x,y)), (200,0,100))) )
                elif color=='orange':
                    image.putpixel( (x, y), tuple(map(operator.add, image.getpixel((x,y)), (200,80,0))) )
                elif color=='purple':
                    image.putpixel( (x, y), tuple(map(operator.add, image.getpixel((x,y)), (80,0,120))) )
                
    image.save(f'{outdir}/seed{seed2}.png')
    storage.child(f"logo/{user_id}/secondlogo.png").put(f'{outdir}/seed{seed2}.png')
    print('SECOND LOGO DONE')
