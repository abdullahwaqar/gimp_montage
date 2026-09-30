#!/usr/bin/env python3

# GIMP 3 Plug-In.
# Create a montage (grid collage) from layers, with live preview.

import math
import sys

import gi

gi.require_version("Gimp", "3.0")
gi.require_version("GimpUi", "3.0")
from gi.repository import Gimp, GimpUi, GLib, GObject

PROC_NAME = "python-fu-montage"
PREVIEW_DELAY_MS = 150


SHAPE_RATIOS = {"square": 1.0, "landscape": 3 / 2, "portrait": 2 / 3}


def auto_grid(layers, gap, shape):
    """Pick columns and rows so the collage matches the target shape
    with as few empty cells as possible."""
    n = len(layers)
    cell_w = max(l.get_width() for l in layers)
    cell_h = max(l.get_height() for l in layers)
    target = SHAPE_RATIOS.get(shape, 1.0)

    best, best_score = (1, n), None
    for cols in range(1, n + 1):
        rows = -(-n // cols)  # ceil
        w = cols * cell_w + (cols + 1) * gap
        h = rows * cell_h + (rows + 1) * gap
        shape_err = abs(math.log((w / h) / target))
        empty = (cols * rows - n) / n
        score = shape_err + empty
        if best_score is None or score < best_score:
            best, best_score = (cols, rows), score
    return best


class MontageBuilder:
    """Builds the collage in a separate image, from the source layers."""

    def __init__(self, src_image):
        self.src_layers = list(src_image.get_layers())
        self.image = Gimp.Image.new_with_precision(
            1, 1, src_image.get_base_type(), src_image.get_precision()
        )
        self.image.undo_disable()
        self.placed = []
        self.display = None

    def render(self, config, fast=False):
        cols = max(1, config.get_property("cols"))
        rows = max(1, config.get_property("rows"))
        order = config.get_property("order")
        fit = config.get_property("fit")
        gap = max(0, config.get_property("spacing"))

        src = list(self.src_layers)
        if order == "bottom-to-top":
            src.reverse()

        if config.get_property("auto"):
            cols, rows = auto_grid(src, gap, config.get_property("shape"))

        src = src[: cols * rows]

        # Clear the previous layout.
        for layer in self.placed:
            self.image.remove_layer(layer)
        self.placed = []

        # Cell size = largest width and largest height among used layers.
        cell_w = max(l.get_width() for l in src)
        cell_h = max(l.get_height() for l in src)

        canvas_w = cols * cell_w + (cols + 1) * gap
        canvas_h = rows * cell_h + (rows + 1) * gap
        self.image.resize(canvas_w, canvas_h, 0, 0)

        Gimp.context_push()
        if fast:
            Gimp.context_set_interpolation(Gimp.InterpolationType.NONE)

        for i, s in enumerate(src):
            layer = Gimp.Layer.new_from_drawable(s, self.image)
            self.image.insert_layer(layer, None, i)
            self.placed.append(layer)

            lw, lh = layer.get_width(), layer.get_height()
            if fit:
                ratio = min(cell_w / lw, cell_h / lh)
                lw = max(1, round(lw * ratio))
                lh = max(1, round(lh * ratio))
                layer.scale(lw, lh, False)

            col, row = i % cols, i // cols
            x = gap + col * (cell_w + gap) + (cell_w - lw) // 2
            y = gap + row * (cell_h + gap) + (cell_h - lh) // 2
            layer.set_offsets(x, y)

        Gimp.context_pop()

        if self.display is None:
            self.display = Gimp.Display.new(self.image)
        Gimp.displays_flush()

    def finish(self):
        self.image.undo_enable()
        Gimp.displays_flush()

    def discard(self):
        if self.display is not None:
            self.display.delete()
            self.display = None


class Montage(Gimp.PlugIn):
    def do_query_procedures(self):
        return [PROC_NAME]

    def do_set_i18n(self, name):
        return False

    def do_create_procedure(self, name):
        procedure = Gimp.ImageProcedure.new(
            self, name, Gimp.PDBProcType.PLUGIN, self.run, None
        )
        procedure.set_image_types("*")
        procedure.set_sensitivity_mask(Gimp.ProcedureSensitivityMask.ALWAYS)
        procedure.set_menu_label("Montage...")
        procedure.add_menu_path("<Image>/Filters/")
        procedure.set_documentation(
            "Arrange layers in a grid",
            "Builds a collage from the image's layers in a new image, "
            "with a live preview while you adjust the settings.",
            name,
        )
        procedure.set_attribution("Crapola (GIMP 3 port)", "Crapola", "2020")

        procedure.add_boolean_argument(
            "auto",
            "Auto grid",
            "Choose columns and rows automatically (ignores Columns/Rows)",
            True,
            GObject.ParamFlags.READWRITE,
        )

        shape = Gimp.Choice.new()
        shape.add("square", 0, "Square", "")
        shape.add("landscape", 1, "Landscape (3:2)", "")
        shape.add("portrait", 2, "Portrait (2:3)", "")
        procedure.add_choice_argument(
            "shape",
            "Auto shape",
            "Target collage shape for Auto grid",
            shape,
            "square",
            GObject.ParamFlags.READWRITE,
        )

        procedure.add_int_argument(
            "cols",
            "Columns",
            "Number of columns",
            1,
            100,
            2,
            GObject.ParamFlags.READWRITE,
        )
        procedure.add_int_argument(
            "rows",
            "Rows",
            "Number of rows",
            1,
            100,
            2,
            GObject.ParamFlags.READWRITE,
        )

        order = Gimp.Choice.new()
        order.add("top-to-bottom", 0, "Top to bottom", "")
        order.add("bottom-to-top", 1, "Bottom to top", "")
        procedure.add_choice_argument(
            "order",
            "Order",
            "Layer order",
            order,
            "top-to-bottom",
            GObject.ParamFlags.READWRITE,
        )

        procedure.add_boolean_argument(
            "fit",
            "Fit photos to cells",
            "Scale each layer to fit its cell, keeping aspect ratio",
            True,
            GObject.ParamFlags.READWRITE,
        )
        procedure.add_int_argument(
            "spacing",
            "Spacing (px)",
            "Gap between cells in pixels",
            0,
            1000,
            0,
            GObject.ParamFlags.READWRITE,
        )
        return procedure

    def run(self, procedure, run_mode, image, drawables, config, run_data):
        if not image.get_layers():
            return procedure.new_return_values(
                Gimp.PDBStatusType.EXECUTION_ERROR,
                GLib.Error.new_literal(
                    GLib.quark_from_string("montage"), "Image has no layers.", 0
                ),
            )

        builder = MontageBuilder(image)

        if run_mode != Gimp.RunMode.INTERACTIVE:
            builder.render(config)
            builder.finish()
            return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())

        GimpUi.init(PROC_NAME)

        # Show the first preview right away.
        builder.render(config, fast=True)

        pending = {"id": 0}

        def do_preview():
            pending["id"] = 0
            builder.render(config, fast=True)
            return False  # run once

        def on_change(cfg, pspec):
            if pending["id"]:
                GLib.source_remove(pending["id"])
            pending["id"] = GLib.timeout_add(PREVIEW_DELAY_MS, do_preview)

        handler = config.connect("notify", on_change)

        dialog = GimpUi.ProcedureDialog.new(procedure, config, "Montage")
        dialog.fill(None)
        ok = dialog.run()
        dialog.destroy()

        config.disconnect(handler)
        if pending["id"]:
            GLib.source_remove(pending["id"])

        if not ok:
            builder.discard()
            return procedure.new_return_values(Gimp.PDBStatusType.CANCEL, GLib.Error())

        # Final render at full quality.
        builder.render(config, fast=False)
        builder.finish()
        return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())


Gimp.main(Montage.__gtype__, sys.argv)
