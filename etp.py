# ##### BEGIN GPL LICENCE BLOCK #####
#  Copyright (C) 2025  Arthur Langlard
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# ##### END GPL LICENCE BLOCK #####


# Start of the project: 10-06-2025
# Last modification: 15-06-2025


import argparse
import pygame
import pygame.freetype
import pickle
import os
from enum import Enum, auto, IntEnum
import numpy


class mode(Enum):
    normal = auto()
    edit = auto()
    axis = auto()

class axis_type(Enum):
    x = auto()
    y = auto()

class marker(IntEnum):
    circle = auto()
    square = auto()
    rhombus = auto()
    triangle = auto()
    triangle_inverted = auto()

class QuitEvent(Exception):
    pass


def analyze_picture(filename):
    """The whole analysis for one image"""

    pygame.init()
    screen = pygame.display.set_mode((1280, 720), pygame.RESIZABLE)
    pygame.display.set_caption("Exhume This Plot")
    clock = pygame.time.Clock()
    running = True
    dt = 0

    asurf = pygame.image.load(filename)

    zoom_factor = 1.0
    screen_gcoord = (0,0) # Top left of the screen
    marker_size = 5.0

    sized_graph = pygame.transform.scale_by(asurf, zoom_factor)
    screen.blit(sized_graph, screen_gcoord)


    # Nomenclature of the positions:
    #
    # pos:      position on the screen, with pixels.
    #
    # gcoord:   global coordinates of objects.
    #           Is equal to pos when scale=1 and no left and
    #           right shifts.
    #           This is internally used to plot all elements
    #           for every scale or left and right shifts.
    #
    # coord:    coordinates of the data points.
    #           The true value of the data that is calculated whith
    #           respect to the axes then exported.

    data_coord = []

    series_gcoord = []
    data_gcoord = [series_gcoord]
    working_series = 0
    
    edit_seriesNo_itemNo = [0,0]

    axes_gcoord = [[(0,0), (100,0)],
                    [(0,100), (0,0)]]
    
    series_marker_size = [marker_size] * len(data_gcoord)
    series_marker_shape = [marker.circle] * len(data_gcoord)

    try:
        with open(filename + ".etp", "rb") as fp:
            chest = pickle.load(fp)
            data_gcoord, axes_gcoord, series_marker_size, series_marker_shape = chest
            working_series = 0
            edit_seriesNo_itemNo = [0,0]
    except FileNotFoundError:
        pass


    def gcoord_to_pos(gcoord, zoom_factor, screen_gcoord):
        """Return the position on the screen from the global coordinates."""
        return pygame.math.Vector2(int(gcoord[0] * zoom_factor - screen_gcoord[0]),
                                int(gcoord[1] * zoom_factor - screen_gcoord[1]))


    def pos_to_gcoord(pos, zoom_factor, screen_gcoord):
        """Return the global coordinates from the position on the screen."""
        return (int((pos[0] + screen_gcoord[0]) / zoom_factor),
                int((pos[1] + screen_gcoord[1]) / zoom_factor))


    def ask_axis(type, zoom_factor, screen_gcoord):
        """Ask the user to define an axis."""
        gcoords = []
        local_running = True

        while local_running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    raise QuitEvent("quit event during axes setup")

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1: # Choose point
                        if len(gcoords) == 0 : gcoords.append(pos_to_gcoord(pygame.mouse.get_pos(), zoom_factor, screen_gcoord))
                        elif len(gcoords) == 1 :
                            if type == axis_type.x:
                                gcoords.append((pos_to_gcoord(pygame.mouse.get_pos(), zoom_factor, screen_gcoord)[0],
                                                gcoords[0][1]))
                            elif type == axis_type.y:
                                gcoords.append((gcoords[0][0],
                                                pos_to_gcoord(pygame.mouse.get_pos(), zoom_factor, screen_gcoord)[1]))
                            local_running = False
                    elif event.button == 3: # Cancel
                        if len(gcoords) == 1:
                            gcoords.pop(0)

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP:
                            screen_gcoord = (screen_gcoord[0], screen_gcoord[1] - 100 * zoom_factor)
                    elif event.key == pygame.K_DOWN:
                        screen_gcoord = (screen_gcoord[0], screen_gcoord[1] + 100 * zoom_factor)
                    elif event.key == pygame.K_RIGHT:
                        screen_gcoord = (screen_gcoord[0] + 100 * zoom_factor, screen_gcoord[1])
                    elif event.key == pygame.K_LEFT:
                        screen_gcoord = (screen_gcoord[0] - 100 * zoom_factor, screen_gcoord[1])
                    elif event.key == pygame.K_SPACE:
                        screen_gcoord = (0,0)
                        zoom_factor = 1.0
                elif event.type == pygame.MOUSEWHEEL:
                    if pygame.key.get_pressed()[pygame.K_LCTRL] or pygame.key.get_pressed()[pygame.K_RCTRL]:
                        zoom_factor = max(0, zoom_factor + event.y*0.1)
                
            
            # Draw temp axis to help plotting the end.
            screen.fill("grey")
            sized_graph = pygame.transform.scale_by(asurf, zoom_factor)
            screen.blit(sized_graph, gcoord_to_pos((0,0), zoom_factor, screen_gcoord))
            if len(gcoords) == 1:
                if type == axis_type.x:
                    pygame.draw.line(screen,
                                    "red",
                                    gcoord_to_pos(gcoords[0], zoom_factor, screen_gcoord),
                                    (pygame.mouse.get_pos()[0], gcoord_to_pos(gcoords[0], zoom_factor, screen_gcoord)[1]))
                elif type == axis_type.y:
                    pygame.draw.line(screen,
                                    "red",
                                    gcoord_to_pos(gcoords[0], zoom_factor, screen_gcoord),
                                    (gcoord_to_pos(gcoords[0], zoom_factor, screen_gcoord)[0], pygame.mouse.get_pos()[1]))
            pygame.display.flip()
            clock.tick(60)

            

        return gcoords[0], gcoords[1]


    def draw_marker(surface, zoom_factor, screen_gcoord, coord, col, marker_size, marker_type, width=0, position=False):
        """Draw a data marker on the screen."""

        # If position==True, screen position is passed instead of gcoord.
        if not position:
            center_pos = gcoord_to_pos(coord, zoom_factor, screen_gcoord)
        else:
            center_pos = screen_gcoord

        if marker_type == marker.circle:
            pygame.draw.circle(surface, col, center_pos, marker_size * zoom_factor, width)
        elif marker_type == marker.square:
            square = pygame.Rect(0, 0, 2 * marker_size * zoom_factor, 2 * marker_size * zoom_factor)
            square.center = center_pos
            pygame.draw.rect(surface, col, square, width)
        elif marker_type == marker.rhombus:
            top_pos     = (center_pos[0], center_pos[1] - marker_size * zoom_factor)
            right_pos   = (center_pos[0] + marker_size * zoom_factor, center_pos[1])
            bottom_pos  = (center_pos[0], center_pos[1] + marker_size * zoom_factor)
            left_pos    = (center_pos[0] - marker_size * zoom_factor, center_pos[1])
            pygame.draw.polygon(surface, col, [top_pos, right_pos, bottom_pos, left_pos], width)
        elif marker_type == marker.triangle:
            top_pos     = (center_pos[0], center_pos[1] - marker_size * zoom_factor)
            right_pos   = (center_pos[0] + marker_size * zoom_factor * 0.86603, center_pos[1] + marker_size * zoom_factor * 0.5)
            left_pos    = (center_pos[0] - marker_size * zoom_factor * 0.86603, center_pos[1] + marker_size * zoom_factor * 0.5)
            pygame.draw.polygon(surface, col, [top_pos, right_pos, left_pos], width)
        elif marker_type == marker.triangle_inverted:
            right_pos   = (center_pos[0] + marker_size * zoom_factor * 0.86603, center_pos[1] - marker_size * zoom_factor * 0.5)
            left_pos    = (center_pos[0] - marker_size * zoom_factor * 0.86603, center_pos[1] - marker_size * zoom_factor * 0.5)
            bottom_pos     = (center_pos[0], center_pos[1] + marker_size * zoom_factor)
            pygame.draw.polygon(surface, col, [right_pos, bottom_pos, left_pos], width)
        

    def draw_data_markers(seriesNo_itemNo, zoom_factor, screen_gcoord, interface_mode=mode.normal):
        """Plot all the data series on the screen.
        Higher transparency in edit mode, except for the current data series.        
        """

        s = pygame.Surface((screen.get_width(),screen.get_height()), pygame.SRCALPHA)
        col = pygame.Color(0,0,0,0)

        seriesNo, _ = seriesNo_itemNo
        
        for i, series_coord in enumerate(data_gcoord):
            alpha = 70
            if interface_mode == mode.edit and i != seriesNo: alpha = 30

            col.hsva = (i*350/len(data_gcoord), 90, 90, alpha)   # Change marker color according to the series.
            for coord in series_coord:
                draw_marker(s, zoom_factor, screen_gcoord, coord, col, series_marker_size[i], series_marker_shape[i])

        screen.blit(s, (0,0))
        return


    def draw_markers_overlay(seriesNo_itemNo, zoom_factor, screen_gcoord):
        """In edit mode, draw an indicator over the edited data point."""
        
        seriesNo, itemNo = seriesNo_itemNo
        s = pygame.Surface((screen.get_width(),screen.get_height()), pygame.SRCALPHA)

        if data_gcoord[seriesNo]:
            coord = data_gcoord[seriesNo][itemNo]
            draw_marker(s, zoom_factor, screen_gcoord, coord, "black", series_marker_size[seriesNo] + 3, series_marker_shape[seriesNo], width = 1)

        screen.blit(s, (0,0))
        return


    def draw_axes(zoom_factor, screen_gcoord):
        """Draw the axes."""
        for axis_coord in axes_gcoord:
            pygame.draw.line(screen,
                            "red",
                            gcoord_to_pos(axis_coord[0], zoom_factor, screen_gcoord),
                            gcoord_to_pos(axis_coord[1], zoom_factor, screen_gcoord))
        return


    def draw_mouse_overlay(zoom_factor, marker_size, marker_shape):
        """Draw a marker under the cursor of the mouse."""
        col = pygame.Color(0,0,0,0)
        col.hsva = (working_series*350/len(data_gcoord), 100, 100, 50)   # Change marker color according to the series.

        pos = pygame.mouse.get_pos()
        coord = pos_to_gcoord(pos, zoom_factor, screen_gcoord)

        draw_marker(screen, zoom_factor, screen_gcoord, coord, col, marker_size, marker_shape)
        return


    def compute_coords():
        """Compute data x and y values based on their coordinates and the axes."""
        x_axis_start_gcoord, x_axis_end_gcoord = axes_gcoord[0]
        y_axis_start_gcoord, y_axis_end_gcoord = axes_gcoord[1]

        data_coord[:] = []

        
        
        for series_gcoord, marker_size in zip(data_gcoord, series_marker_size):
            data_array = numpy.zeros((len(series_gcoord), 4))
            for i, gcoord in enumerate(series_gcoord):
                x_gcoord, y_gcoord = gcoord
                data_array[i, 0] = (x_gcoord - x_axis_start_gcoord[0]) / (x_axis_end_gcoord[0] - x_axis_start_gcoord[0])
                data_array[i, 2] = (y_gcoord - y_axis_start_gcoord[1]) / (y_axis_end_gcoord[1] - y_axis_start_gcoord[1])
                data_array[i, 1] = max(1.0, marker_size * zoom_factor) / (x_axis_end_gcoord[0] - x_axis_start_gcoord[0])
                data_array[i, 3] = -max(1.0, marker_size * zoom_factor) / (y_axis_end_gcoord[1] - y_axis_start_gcoord[1])
            data_coord.append(data_array)
        
        return


    def export_data():
        """Export data x and y values in a file."""
        for i, data_array in enumerate(data_coord):
            numpy.savetxt(filename + "_" + str(i) + ".csv", data_array, delimiter='\t', comments='', fmt='%1.7f', header="X\t+-\tY\t+-")


    def save():
        """Save the working environment."""
        chest = [data_gcoord, axes_gcoord, series_marker_size, series_marker_shape]
        with open(filename + ".etp", "wb") as fp:
            pickle.dump(chest, fp)


    def draw_controls_overlay(interface_mode, display_controls):
        """Display the controls."""

        default_font = pygame.freetype.SysFont(None, 16)
        default_font.antialiased = True

        if interface_mode == mode.normal:
            text_string_a = "E: EDIT mode   M: marker shape   Mouse Wheel: marker size   Left click: Add marker   Right click: remove last marker"
            text_string_b = "CTRL+Wheel: zoom   Arrows: Move view   SPACE: reset view   S: save   C: compute and export data"
            text_string_c = "RETURN: add a new series of data   P: previous series   N: next series"
            text_string_d = "H: hide/show controls   X or Y: set X- or Y- axis"

            text_strings = [text_string_a, text_string_b, text_string_c, text_string_d]
            text_origin = screen.get_height()
            text_mode_Rect = default_font.get_rect("NORMAL") # Top origin of the text
            text_origin -= text_mode_Rect.height
            
            s = pygame.Surface((screen.get_width(),screen.get_height()), pygame.SRCALPHA)
            pygame.draw.rect(s,
                             (100, 100, 100),
                             pygame.Rect(0, text_origin, screen.get_width(), text_mode_Rect.height))
            default_font.render_to(s, (0, text_origin), "NORMAL", (255, 255, 255)).height
            if display_controls:
                for text_string in text_strings:
                    text_origin -= default_font.get_rect(text_string).height
                    default_font.render_to(s, (0, text_origin), text_string, (0, 0, 0), bgcolor= (255, 255, 255, 200)).height
                
            screen.blit(s, (0,0))
            
        elif interface_mode == mode.edit:
            text_string_a = "ESCAPE: NORMAL mode   LEFT (+SHIFT): previous data point   RIGHT (+SHIFT): next data point   HOME: first data point   END: last data point"
            text_string_b = "CTRL+Wheel: zoom   WASD: Move data point"
            text_string_c = "   SHIFT+HOME: first series   SHIFT+END: last series"
            text_string_d = "SUPPR: Remove data point   SHIFT+SUPPR: Remove data series   DOWN (+SHIFT): next series   UP (+SHIFT): previous series"
            text_string_e = "H: hide/show controls"

            text_strings = [text_string_a, text_string_b, text_string_c, text_string_d, text_string_e]
            text_origin = screen.get_height()
            text_mode_Rect = default_font.get_rect("EDIT") # Top origin of the text
            text_origin -= text_mode_Rect.height
            
            s = pygame.Surface((screen.get_width(),screen.get_height()), pygame.SRCALPHA)
            pygame.draw.rect(s,
                             (100, 100, 100),
                             pygame.Rect(0, text_origin, screen.get_width(), text_mode_Rect.height))
            default_font.render_to(s, (0, text_origin), "EDIT", (255, 255, 255)).height
            if display_controls:
                for text_string in text_strings:
                    text_origin -= default_font.get_rect(text_string).height
                    default_font.render_to(s, (0, text_origin), text_string, (0, 0, 0), bgcolor= (255, 255, 255, 200)).height
                
            screen.blit(s, (0,0))

    interface_mode = mode.normal
    display_controls = True

    while running:

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                
            elif event.type == pygame.MOUSEWHEEL:
                if pygame.key.get_pressed()[pygame.K_LCTRL] or pygame.key.get_pressed()[pygame.K_RCTRL]:
                    zoom_factor = max(0, zoom_factor + event.y*0.1)
                else:
                    series_marker_size[working_series] = max(1, series_marker_size[working_series] + event.y)


            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1: # Left click
                    pos = pygame.mouse.get_pos()

                    if interface_mode == mode.normal:
                        data_gcoord[working_series].append(pos_to_gcoord(pos, zoom_factor, screen_gcoord))
                    
                
                elif event.button == 3: # Right click
                    if interface_mode == mode.normal:
                        if len(data_gcoord[working_series]) > 0 : data_gcoord[working_series].pop(-1)
                

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_e:
                    interface_mode = mode.edit

                elif event.key == pygame.K_ESCAPE:
                    interface_mode = mode.normal
                    working_series = 0

                elif event.key == pygame.K_RETURN:   # Add a series
                    if interface_mode == mode.normal:
                        data_gcoord.append([])
                        series_marker_size.append(marker_size)
                        series_marker_shape.append(marker.circle)
                        working_series = len(data_gcoord) - 1

                elif event.key == pygame.K_n:   # Next series
                    if interface_mode == mode.normal:
                        working_series = (working_series + 1) % len(data_gcoord)

                elif event.key == pygame.K_p:   # Prev series
                    if interface_mode == mode.normal:
                        working_series = (working_series - 1) % len(data_gcoord)
                
                elif event.key == pygame.K_m:   # Marker shape
                    if interface_mode == mode.normal:
                        series_marker_shape[working_series] = 1 + ((series_marker_shape[working_series]) % len(marker))
                        
                elif event.key == pygame.K_x:   # Set x-axis
                    try:
                        start_coord, stop_coord = ask_axis(axis_type.x, zoom_factor, screen_gcoord)
                        axes_gcoord[0] = [start_coord, stop_coord]
                    except QuitEvent:
                        running = False

                elif event.key == pygame.K_y:   # Set y-axis
                    try:
                        start_coord, stop_coord = ask_axis(axis_type.y, zoom_factor, screen_gcoord)
                        axes_gcoord[1] = [start_coord, stop_coord]
                    except QuitEvent:
                        running = False

                elif event.key == pygame.K_UP:
                    if interface_mode == mode.normal:
                        screen_gcoord = (screen_gcoord[0], screen_gcoord[1] - 100 * zoom_factor)
                    elif interface_mode == mode.edit:
                        step = 1
                        if pygame.key.get_pressed()[pygame.K_RSHIFT] or pygame.key.get_pressed()[pygame.K_LSHIFT]:
                            step = 10
                        edit_seriesNo_itemNo = [(edit_seriesNo_itemNo[0] - step) % len(data_gcoord), 0]

                elif event.key == pygame.K_DOWN:
                    if interface_mode == mode.normal:
                        screen_gcoord = (screen_gcoord[0], screen_gcoord[1] + 100 * zoom_factor)
                    elif interface_mode == mode.edit:
                        step = 1
                        if pygame.key.get_pressed()[pygame.K_RSHIFT] or pygame.key.get_pressed()[pygame.K_LSHIFT]:
                            step = 10
                        edit_seriesNo_itemNo = [(edit_seriesNo_itemNo[0] + step) % len(data_gcoord), 0]

                elif event.key == pygame.K_RIGHT:
                    if interface_mode == mode.normal:
                        screen_gcoord = (screen_gcoord[0] + 100 * zoom_factor, screen_gcoord[1])
                    elif interface_mode == mode.edit:
                        if data_gcoord[edit_seriesNo_itemNo[0]]:
                            step = 1
                            if pygame.key.get_pressed()[pygame.K_RSHIFT] or pygame.key.get_pressed()[pygame.K_LSHIFT]:
                                step = 10
                            edit_seriesNo_itemNo[1] = (edit_seriesNo_itemNo[1] + step) % len(data_gcoord[edit_seriesNo_itemNo[0]])

                elif event.key == pygame.K_LEFT:
                    if interface_mode == mode.normal:
                        screen_gcoord = (screen_gcoord[0] - 100 * zoom_factor, screen_gcoord[1])
                    elif interface_mode == mode.edit:
                        if data_gcoord[edit_seriesNo_itemNo[0]]:
                            step = 1
                            if pygame.key.get_pressed()[pygame.K_RSHIFT] or pygame.key.get_pressed()[pygame.K_LSHIFT]:
                                step = 10
                            edit_seriesNo_itemNo[1] = (edit_seriesNo_itemNo[1] - step) % len(data_gcoord[edit_seriesNo_itemNo[0]])
                
                elif event.key == pygame.K_HOME:
                    if interface_mode == mode.edit:
                        if pygame.key.get_pressed()[pygame.K_RSHIFT] or pygame.key.get_pressed()[pygame.K_LSHIFT]:
                            edit_seriesNo_itemNo[0] = 0
                        else:
                            edit_seriesNo_itemNo[1] = 0

                elif event.key == pygame.K_END:
                    if interface_mode == mode.edit:
                        if pygame.key.get_pressed()[pygame.K_RSHIFT] or pygame.key.get_pressed()[pygame.K_LSHIFT]:
                            edit_seriesNo_itemNo[0] = len(data_gcoord) - 1
                        else:
                            edit_seriesNo_itemNo[1] = len(data_gcoord[edit_seriesNo_itemNo[0]]) - 1

                elif event.key == pygame.K_SPACE:
                    if interface_mode == mode.normal:
                        screen_gcoord = (0,0)
                        zoom_factor = 1.0
                        
                elif event.key == pygame.K_w:
                    if interface_mode == mode.edit:
                        x_gcoord, y_gcoord = data_gcoord[edit_seriesNo_itemNo[0]][edit_seriesNo_itemNo[1]]
                        data_gcoord[edit_seriesNo_itemNo[0]][edit_seriesNo_itemNo[1]] = (x_gcoord, y_gcoord - 1)

                elif event.key == pygame.K_s:
                    if interface_mode == mode.edit:
                        x_gcoord, y_gcoord = data_gcoord[edit_seriesNo_itemNo[0]][edit_seriesNo_itemNo[1]]
                        data_gcoord[edit_seriesNo_itemNo[0]][edit_seriesNo_itemNo[1]] = (x_gcoord, y_gcoord + 1)
                    elif interface_mode == mode.normal:
                        save()

                elif event.key == pygame.K_a:
                    if interface_mode == mode.edit:
                        x_gcoord, y_gcoord = data_gcoord[edit_seriesNo_itemNo[0]][edit_seriesNo_itemNo[1]]
                        data_gcoord[edit_seriesNo_itemNo[0]][edit_seriesNo_itemNo[1]] = (x_gcoord - 1, y_gcoord)

                elif event.key == pygame.K_d:
                    if interface_mode == mode.edit:
                        x_gcoord, y_gcoord = data_gcoord[edit_seriesNo_itemNo[0]][edit_seriesNo_itemNo[1]]
                        data_gcoord[edit_seriesNo_itemNo[0]][edit_seriesNo_itemNo[1]] = (x_gcoord + 1, y_gcoord)

                elif event.key == pygame.K_DELETE:
                    if interface_mode == mode.edit:
                        if pygame.key.get_pressed()[pygame.K_RSHIFT] or pygame.key.get_pressed()[pygame.K_LSHIFT]: # Remove the whole series
                            if len(data_gcoord) > 1:
                                data_gcoord.pop(edit_seriesNo_itemNo[0])
                                edit_seriesNo_itemNo[0] = max(0, edit_seriesNo_itemNo[0] - 1)
                                edit_seriesNo_itemNo[1] = 0
                            else:
                                data_gcoord[0] = []
                                edit_seriesNo_itemNo[0]
                                edit_seriesNo_itemNo[1] = 0
                        elif len(data_gcoord[edit_seriesNo_itemNo[0]]) > 0:   # Remove this element from the series.
                            data_gcoord[edit_seriesNo_itemNo[0]].pop(edit_seriesNo_itemNo[1])
                            edit_seriesNo_itemNo[1] = max(0, edit_seriesNo_itemNo[1] - 1)
                            
                elif event.key == pygame.K_c:   # Compute actual coordinates with the axes.
                    if interface_mode == mode.normal:
                        compute_coords()
                        export_data()

                elif event.key == pygame.K_h:
                    display_controls = not display_controls

            if running:
                screen.fill("grey")
                sized_graph = pygame.transform.scale_by(asurf, zoom_factor)
                screen.blit(sized_graph, gcoord_to_pos((0,0), zoom_factor, screen_gcoord))
                draw_axes(zoom_factor, screen_gcoord)
                draw_data_markers(edit_seriesNo_itemNo, zoom_factor, screen_gcoord, interface_mode)

                if interface_mode == mode.edit:
                    draw_markers_overlay(edit_seriesNo_itemNo, zoom_factor, screen_gcoord)
                else:
                    draw_mouse_overlay(zoom_factor, series_marker_size[working_series], series_marker_shape[working_series])
                draw_controls_overlay(interface_mode, display_controls)

                pygame.display.flip()


        dt = clock.tick(60) / 1000

    pygame.quit()





parser = argparse.ArgumentParser()
parser.add_argument('files', nargs='*', help="Files")
args = parser.parse_args()
print("files:", args.files)
filenames = [filename for filename in args.files]
for filename in filenames:
    analyze_picture(filename)