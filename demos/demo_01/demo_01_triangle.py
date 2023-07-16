import numpy as np
import moderngl as mgl
from core.window import Window


class TriangleApp(Window):

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.context = mgl.create_context()
        self.program = None
        self.vertices = None
        self.vao = None
        self.vbo = None

    def setup(self):
        self.program = self.context.program(
            vertex_shader='''
            #version 330
            
            in vec2 in_vert;
            
            in vec3 in_color;
            out vec3 v_color;    // Goes to the fragment shader
            
            void main() {
               gl_Position = vec4(in_vert, 0.0, 1.0);
               v_color = in_color;
            }
            ''',
            fragment_shader='''
            #version 330
            
            in vec3 v_color;
            out vec4 f_color;
            
            void main() {
                // We're not interested in changing the alpha value
                f_color = vec4(v_color, 1.0);
            }
            ''',
        )

        self.vertices = np.array([
            # x, y, red, green, blue
            0.0, 0.8, 1.0, 0.0, 0.0,
            -0.6, -0.8, 0.0, 1.0, 0.0,
            0.6, -0.8, 0.0, 0.0, 1.0,
        ], dtype='f4')

        self.vbo = self.context.buffer(self.vertices)

        # We control the 'in_vert' and `in_color' variables
        self.vao = self.context.vertex_array(
            self.program,
            [
                # Map in_vert to the first 2 floats
                # Map in_color to the next 3 floats
                (self.vbo, '2f 3f', 'in_vert', 'in_color')
            ],
        )

    def render(self):
        self.context.clear(0.0, 0.0, 0.0)
        self.vao.render()


def main():

    app = TriangleApp(
        window_size=(800, 600),
        window_title="First Window - A Simple Triangle",
        vertical_sync=True,
        enable_imgui=False
    )

    app.run()


if __name__ == "__main__":
    main()