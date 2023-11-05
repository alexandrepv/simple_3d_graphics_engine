#version 400

#if defined VERTEX_SHADER

in float in_command_id;
in vec2 in_position;
in vec2 in_size;
in float in_edge_width;
in vec4 in_color;
in vec2 in_uv_min;
in vec2 in_uv_max;

flat out int gs_command_id;
out vec2 gs_position;
out vec2 gs_size;
out float gs_edge_width;
out vec4 gs_color;
out vec2 gs_uv_min;
out vec2 gs_uv_max;


flat out int command_id;


void main() {

    gs_command_id = int(in_command_id);  // Command IDs come in float for the sake of simplicity
    gs_position = in_position;
    gs_size = in_size;
    gs_edge_width = in_edge_width;
    gs_color = in_color;
    gs_uv_min = in_uv_min;
    gs_uv_max = in_uv_max;

    gl_Position = vec4(in_position, 0.0, 1.0);
}


#elif defined GEOMETRY_SHADER

// TODO: Move these definitions to another file and include them here instead
#define COMMAND_ID_AABB_FILLED  0
#define COMMAND_ID_AABB_EDGE    1
#define COMMAND_ID_CHARACTER    2


layout (points) in;
layout (triangle_strip, max_vertices=8) out;

uniform mat4 projection_matrix; // Your projection matrix

// The inputs are expected to be arrays because you could be providing
// multiple points, like a line (2 points) and so on.
// The POINTS rendering mode means this is a 1-element array, hence
// the gs_position[0] :)

flat in int gs_command_id[];
in vec2 gs_position[];
in vec2 gs_size[];
in float gs_edge_width[];
in vec4 gs_color[];
in vec2 gs_uv_min[];
in vec2 gs_uv_max[];


flat out int command_id;
out vec2 uv;
out vec4 geometry_color;

void emitVertexWithUV(vec2 position, vec2 uvCoords) {
    gl_Position = projection_matrix * vec4(position, 0.0, 1.0);
    uv = uvCoords;
    EmitVertex();
}

void main() {

    // Calculate the rectangle vertex position
    vec2 position = gs_position[0].xy;
    vec2 size = gs_size[0].xy;

    command_id = gs_command_id[0];

    if (command_id == COMMAND_ID_CHARACTER){

        emitVertexWithUV(position, gs_uv_min[0]);
        emitVertexWithUV(position + vec2(0, gs_size[0].y), vec2(gs_uv_min[0].x, gs_uv_max[0].y));
        emitVertexWithUV(position + vec2(gs_size[0].x, 0), vec2(gs_uv_max[0].x, gs_uv_min[0].y));
        emitVertexWithUV(position + vec2(gs_size[0].x, gs_size[0].y), vec2(gs_uv_max[0].x, gs_uv_max[0].y));

    } else if (command_id == COMMAND_ID_AABB_FILLED){

        vec2 fill_0 = position;
        vec2 fill_1 = vec2(position.x, position.y + size.y );
        vec2 fill_2 = vec2(position.x + size.x, position.y);
        vec2 fill_3 = vec2(position.x + size.x, position.y + size.y);

        // =========[ Draw Fill ]==========

        geometry_color = gs_color[0].rgba;

        // Triangle A)
        gl_Position = projection_matrix * vec4(fill_0, 0.0, 1.0);
        EmitVertex();

        gl_Position = projection_matrix * vec4(fill_1, 0.0, 1.0);
        EmitVertex();

        gl_Position = projection_matrix * vec4(fill_2, 0.0, 1.0);
        EmitVertex();

        gl_Position = projection_matrix * vec4(fill_3, 0.0, 1.0);
        EmitVertex();

        // Draw Edge (if it exists)

    }




    EndPrimitive();
}


#elif defined FRAGMENT_SHADER

// TODO: Move these definitions to another file and include them here instead
#define COMMAND_ID_AABB_FILLED  0
#define COMMAND_ID_AABB_EDGE    1
#define COMMAND_ID_CHARACTER    2

uniform sampler2D font_texture;

// uniform vec3 font_color = vec3(1.0, 1.0, 1.0);

flat in int command_id;
in vec2 uv;
in vec4 geometry_color;

out vec4 frag_color;


void main()
{

    if (command_id == COMMAND_ID_AABB_FILLED){
        frag_color = geometry_color;
    } else if (command_id == COMMAND_ID_CHARACTER){
        float texture_color = texture(font_texture, uv).r;
        frag_color =  vec4(1.0, 1.0, 1.0, texture_color);

    }

}

#endif
