#!/usr/bin/env python
# coding: utf-8
from PIL import Image
from StringIO import StringIO
import json
import re
import requests

artsy_url = raw_input("Enter the Artsy URL of the painting you'd like to download: ")

response = requests.get(artsy_url)
if not response.status_code == 200:
  raise Exception('Bad response from Artsy, cannot get the page you asked for.')

painting_data_match_groups = re.search(r'\$.parseJSON\(("{.*dztiles.*}")\)\)\);',
                                       response.content).groups()
if not painting_data_match_groups:
  raise Exception('Could not find any painting data on that page.')

painting_data = json.loads(json.loads(painting_data_match_groups[0]))
images = painting_data.get('images')
if not images:
  raise Exception('Could not find image data for the requested painting.')

if len(images) > 1:
  raise Exception('There are too many images in the painting data!', len(images))

image_data = images[0]

tile_base_url = image_data.get('tile_base_url')
if not tile_base_url:
  raise Exception('Could not find a tile base URL in the image data.')

tile_format = image_data.get('tile_format')
if not tile_format:
  raise Exception('Could not find a tile format in the image data.')

tile_size_px = image_data.get('tile_size')
image_width_px = image_data.get('max_tiled_width')
image_height_px = image_data.get('original_height')

x_count = int(image_width_px / tile_size_px) + 1
y_count = int(image_height_px / tile_size_px) + 1

# This is the template string that we can fill out to download a given tile.
# There are various different tileset_ids of different sizes, so we iterate
# through them to try to find the largest available tileset_id.
tile_url_template = ''.join((tile_base_url,
                             '/{tileset_id}/{x}_{y}.',
                             tile_format))
tileset_id = 0
for _id in xrange(0, 20):
  tile_url = tile_url_template.format(tileset_id=_id, x=0, y=0)
  response = requests.get(tile_url)
  # All of the tiles are served via S3, and we get a 404 response when
  # the requeset tile is not available. This usually means that we've passed
  # the largest tileset available, so we can stop looking for larger ones.
  if response.status_code != 200:
    break

  tileset_id = _id

print 'Beginning download...'

final_image = Image.new('RGB', (image_width_px, image_height_px))
for i in xrange(x_count):
  for j in xrange(y_count):
    tile_url = tile_url_template.format(tileset_id=tileset_id, x=i, y=j)
    print '\rDownloading tile from {}'.format(tile_url)
    response = requests.get(tile_url)
    tile_image = Image.open(StringIO(response.content))
    final_image.paste(tile_image, (i * tile_size_px, j * tile_size_px))

image_name = painting_data.get('id', 'artsy-output')
file_name = image_name + '.' + tile_format
final_image.save(file_name)
print 'Done! Downloaded to {} at {}x{}'.format(file_name,
                                               image_width_px,
                                               image_height_px)

