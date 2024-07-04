#version 330

#if defined VERTEX_SHADER

uniform mat4 uViewProjMatrix;

layout(location = 0) in vec4 aPositionSize;
layout(location = 1) in vec4 aColor;

out VertexData {
    noperspective float m_edgeDistance;
    noperspective float m_size;
    smooth vec4 m_color;
} vData;

void main() {
    vData.m_color = aColor;  // Directly pass the color without swizzling
    vData.m_color.a *= smoothstep(0.0, 1.0, aPositionSize.w / 2.0);
    vData.m_size = max(aPositionSize.w, 2.0);
    gl_Position = uViewProjMatrix * vec4(aPositionSize.xyz, 1.0);
}

#elif defined GEOMETRY_SHADER

layout(lines) in;
layout(triangle_strip, max_vertices = 4) out;

uniform vec2 uViewport;

in VertexData {
    noperspective float m_edgeDistance;
    noperspective float m_size;
    smooth vec4 m_color;
} vData[];

out VertexData {
    noperspective float m_edgeDistance;
    noperspective float m_size;
    smooth vec4 m_color;
} vDataOut;

void main() {
    vec2 pos0 = gl_in[0].gl_Position.xy / gl_in[0].gl_Position.w;
    vec2 pos1 = gl_in[1].gl_Position.xy / gl_in[1].gl_Position.w;

    vec2 dir = pos1 - pos0;
    dir = normalize(vec2(dir.x, dir.y * uViewport.y / uViewport.x)); // correct for aspect ratio
    vec2 tng0 = vec2(-dir.y, dir.x) * vData[0].m_size / uViewport;
    vec2 tng1 = vec2(-dir.y, dir.x) * vData[1].m_size / uViewport;

    // Line start
    gl_Position = vec4((pos0 - tng0) * gl_in[0].gl_Position.w, gl_in[0].gl_Position.zw);
    vDataOut.m_edgeDistance = -vData[0].m_size;
    vDataOut.m_size = vData[0].m_size;
    vDataOut.m_color = vData[0].m_color;
    EmitVertex();

    gl_Position = vec4((pos0 + tng0) * gl_in[0].gl_Position.w, gl_in[0].gl_Position.zw);
    vDataOut.m_edgeDistance = vData[0].m_size;
    vDataOut.m_size = vData[0].m_size;
    vDataOut.m_color = vData[0].m_color;
    EmitVertex();

    // Line end
    gl_Position = vec4((pos1 - tng1) * gl_in[1].gl_Position.w, gl_in[1].gl_Position.zw);
    vDataOut.m_edgeDistance = -vData[1].m_size;
    vDataOut.m_size = vData[1].m_size;
    vDataOut.m_color = vData[1].m_color;
    EmitVertex();

    gl_Position = vec4((pos1 + tng1) * gl_in[1].gl_Position.w, gl_in[1].gl_Position.zw);
    vDataOut.m_edgeDistance = vData[1].m_size;
    vDataOut.m_size = vData[1].m_size;
    vDataOut.m_color = vData[1].m_color;
    EmitVertex();

    EndPrimitive();
}

#elif defined FRAGMENT_SHADER

in VertexData {
    noperspective float m_edgeDistance;
    noperspective float m_size;
    smooth vec4 m_color;
} vData;

layout(location=0) out vec4 fResult;

void main() {
    fResult = vData.m_color;
    float d = abs(vData.m_edgeDistance) / vData.m_size;
    d = smoothstep(1.0, 1.0 - (2.0 / vData.m_size), d);
    fResult.a *= d;
}
#endif
