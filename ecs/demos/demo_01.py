from ecs import constants
from ecs.editor import Editor
from ecs.systems.imgui_system.imgui_system import IMGUISystem
from ecs.systems.render_system.render_system import RenderSystem


def main():

    editor = Editor(
        window_size=(1024, 768),
        window_title="Basic Scene Demo",
        vertical_sync=True
    )

    editor.register_system(name="imgui_system",
                           system=IMGUISystem(),
                           subscribed_events=[
                               constants.EVENT_MOUSE_SCROLL,
                           ])

    editor.register_system(name="render_system",
                           system=RenderSystem(),
                           subscribed_events=[
                           ])

    entity_uid = editor.component_pool.create_entity()
    editor.component_pool.add_component(entity_uid=entity_uid,
                                        component_type=constants.COMPONENT_TYPE_TRANSFORM)

    mesh = editor.component_pool.add_component(entity_uid=entity_uid,
                                               component_type=constants.COMPONENT_TYPE_MESH,
                                               shape=constants.MESH_SHAPE_FROM_OBJ,
                                               fpath=r"D:\git_repositories\alexandrepv\simple_3d_graphics_enigne\resources\models\dragon.obj")
    editor.component_pool.add_component(entity_uid=entity_uid,
                                        component_type=constants.COMPONENT_TYPE_RENDERABLE)

    editor.run()


if __name__ == "__main__":
    main()
