from src.core.editor import Editor
import scalene


def main():

    editor = Editor(window_title="Basic Scene Demo", vertical_sync=False)

    editor.load_scene(scene_xml_fpath="demos/demo_01_basic_scene/basic_scene.xml")

    editor.run()


if __name__ == "__main__":
    main()
