import time


def millis():
    return int(time.time() * 1000)


def rgb_to_hex(r, g, b, normalized=True):
    if normalized:
        return '#%02x%02x%02x' % (r * 255, g * 255, b * 255)
    else:
        return '#%02x%02x%02x' % (r, g, b)


def rgb_tuple_to_hex(rgb, normalized=True):
    return rgb_to_hex(rgb[0], rgb[1], rgb[2], normalized)


def blend_colors(color1, color2, weight):
    r1, g1, b1 = color1
    r2, g2, b2 = color2
    r = r1 * weight + r2 * (1 - weight)
    g = g1 * weight + g2 * (1 - weight)
    b = b1 * weight + b2 * (1 - weight)
    return (r, g, b)
