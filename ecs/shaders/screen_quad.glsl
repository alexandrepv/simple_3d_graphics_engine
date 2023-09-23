#version 400

#if defined VERTEX_SHADER

in vec3 in_vert;
in vec2 in_uv;

out vec2 uv;

void main() {
    gl_Position = vec4(in_vert, 1);
    uv = in_uv;
}

#elif defined FRAGMENT_SHADER

in vec2 uv;

// Input textures
uniform sampler2D color_texture;
uniform sampler2D normal_texture;
uniform sampler2D viewpos_texture;
uniform sampler2D entity_info_texture;
uniform sampler2D selection_texture;
uniform sampler2D depth_texture;

// Other input uniforms
uniform vec3 outline_color = vec3(1.0, 0.65, 0.0);  // Default orange color used in Blender
uniform int selected_texture = 0;

out vec4 fragColor;

// MurmurHash3 32-bit finalizer.
uint hash(uint h) {
    h ^= h >> 16;
    h *= 0x85ebca6bu;
    h ^= h >> 13;
    h *= 0xc2b2ae35u;
    h ^= h >> 16;
    return h;
}

// Hash an int value and return a color.
vec3 int_to_color(uint i) {
    uint h = hash(i);

    vec3 c = vec3(
        (h >>  0u) & 255u,
        (h >>  8u) & 255u,
        (h >> 16u) & 255u
    );

    return c * (1.0 / 255.0);
}

vec3 calculate_outline_color();
float LinearizeDepth(float depthValue);

void main() {

    vec3 color_rgb;

    if (selected_texture == 0) {
        // Color
        color_rgb = calculate_outline_color();

    } else if (selected_texture == 1) {
        // Normal
        color_rgb = texture(normal_texture, uv).rgb;

    } else if (selected_texture == 2) {
        // Viewpos
        color_rgb = texture(viewpos_texture, uv).xyz;

    } else if (selected_texture == 3) {
        // Entity ID
        uint id = floatBitsToUint(texture(entity_info_texture, uv).r);
        color_rgb = int_to_color(id);

    } else if (selected_texture == 4) {
        // Current Selection
        color_rgb = texture(selection_texture, uv).rgb;

    } else if (selected_texture == 5) {
        // Depth
        float depth = texture(depth_texture, uv).r;
        depth = LinearizeDepth(depth);
        color_rgb = vec3(depth);

    }

    fragColor = vec4(color_rgb, 1.0);
}

float LinearizeDepth(float depthValue) {
    float zNear = 0.1; // Adjust this to match your scene's near clipping plane
    float zFar = 100.0; // Adjust this to match your scene's far clipping plane
    return (2.0 * zNear) / (zFar + zNear - depthValue * (zFar - zNear));
}

vec3 calculate_outline_color(){

    // TODO: Fix issue where outline roll over to the other edge of the screen

    // Sample the silhouette texture
    vec3 silhouette_color = texture(selection_texture, uv).rgb;

    // Check if the pixel is part of the object silhouette
    bool is_silhouette = silhouette_color.r == 1.0;

    // Sample the neighboring pixels
    float top_left = textureOffset(selection_texture, uv, ivec2(-1, -1)).r;
    float top = textureOffset(selection_texture, uv, ivec2(0, -1)).r;
    float top2 = textureOffset(selection_texture, uv, ivec2(0, -2)).r;
    float top_right = textureOffset(selection_texture, uv, ivec2(1, -1)).r;

    float left2 = textureOffset(selection_texture, uv, ivec2(-2, 0)).r;
    float left = textureOffset(selection_texture, uv, ivec2(-1, 0)).r;
    float right = textureOffset(selection_texture, uv, ivec2(1, 0)).r;
    float right2 = textureOffset(selection_texture, uv, ivec2(2, 0)).r;

    float bottom_left = textureOffset(selection_texture, uv, ivec2(-1, 1)).r;
    float bottom = textureOffset(selection_texture, uv, ivec2(0, 1)).r;
    float bottom2 = textureOffset(selection_texture, uv, ivec2(0, 2)).r;
    float bottom_right = textureOffset(selection_texture, uv, ivec2(1, 1)).r;

    // Check if any neighboring pixel is not part of the silhouette
    bool is_edge = !is_silhouette && (
        top_left == 1.0 ||
        top == 1.0 ||
        top2 == 1.0 ||
        top_right == 1.0 ||
        left2 == 1.0 ||
        left == 1.0 ||
        right == 1.0 ||
        right2 == 1.0 ||
        bottom_left == 1.0 ||
        bottom == 1.0 ||
        bottom2 == 1.0 ||
        bottom_right == 1.0
    );

    // If pixel is an edge, apply the outline color
    // Otherwise, use the original texture color
    return is_edge ? outline_color : texture(color_texture, uv).rgb;
}


#endif
