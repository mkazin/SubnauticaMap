from utilities.geometry import geographical_distance, pol2cart # reverse_bearing


class Charting(object):

    @staticmethod
    def get_cartesean_coords(tunnel_distance, depth, bearing):
        try:
            surface_distance = geographical_distance(
                tunnel_distance=tunnel_distance, depth=depth)
        except KeyError:
            print('Warning: missing depth on marker: {0}'.format(mark))
            surface_distance = tunnel_distance

        # Convert polar coordinate information to Cartesian coordinates (x, y)
        return pol2cart(surface_distance, bearing)

    @staticmethod
    def get_plot_data(markers):
        output = []
        for mark in markers:
            marker = {
                'id': str(mark.id),
                'x': mark.x, 'y': mark.y,
                'depth': int(mark.depth),
                'bearing': int(mark.bearing),
                'distance': int(mark.distance),
                'name': mark.name,
                'marker_type': str(mark.marker_type_name),
                'color': mark.color
            }
            output.append(marker)
        return output
