import struct

import ModernGL
from PyQt5 import QtCore, QtOpenGL, QtWidgets


class QGLControllerWidget(QtOpenGL.QGLWidget):
    def __init__(self):
        fmt = QtOpenGL.QGLFormat()
        fmt.setVersion(3, 3)
        fmt.setProfile(QtOpenGL.QGLFormat.CoreProfile)
        fmt.setSampleBuffers(True)
        self.timer = QtCore.QElapsedTimer()
        super(QGLControllerWidget, self).__init__(fmt, None)

    def initializeGL(self):
        self.ctx = ModernGL.create_context()

        prog = self.ctx.program(
            vertex_shader='''
                #version 330

                in vec2 vert;

                in vec4 vert_color;
                out vec4 frag_color;

                uniform vec2 scale;
                uniform float rotation;

                void main() {
                    frag_color = vert_color;
                    float r = rotation * (0.5 + gl_InstanceID * 0.05);
                    mat2 rot = mat2(cos(r), sin(r), -sin(r), cos(r));
                    gl_Position = vec4((rot * vert) * scale, 0.0, 1.0);
                }
            '''),
            fragment_shader='''
                #version 330

                in vec4 frag_color;
                out vec4 color;

                void main() {
                    color = vec4(frag_color);
                }
            '''),
        ])

        self.scale = prog.uniforms['scale']
        self.rotation = prog.uniforms['rotation']

        vbo = self.context.buffer(struct.pack(
            '18f',
            1.0, 0.0, 1.0, 0.0, 0.0, 0.5,
            -0.5, 0.86, 0.0, 1.0, 0.0, 0.5,
            -0.5, -0.86, 0.0, 0.0, 1.0, 0.5,
        ))

        self.vao = self.context.simple_vertex_array(prog, vbo, ['vert', 'vert_color'])

        self.timer.restart()

    def paintGL(self):
        self.context.viewport = (0, 0, self.width_pixels(), self.height_pixels())
        self.context.clear(0.9, 0.9, 0.9)
        self.scale.value = (self.height_pixels() / self.width_pixels() * 0.75, 0.75)
        self.rotation.value = self.timer.elapsed() / 1000
        self.context.enable(ModernGL.BLEND)
        self.vao.render(instances=10)
        self.context.finish()
        self.update_dimensions()


app = QtWidgets.QApplication([])
window = QGLControllerWidget()
window.move(QtWidgets.QDesktopWidget().rect().center() - window.rect().center())
window.show()
app.exec_()
