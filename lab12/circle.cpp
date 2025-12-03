#include <GL/glew.h>
#include <GL/glut.h>
#include <iostream>
#include <vector>
#include <cmath>

GLuint vbo = 0;
GLuint shaderProgram = 0;

GLint uniformScaleLoc = -1;

float scaleX = 1.0f;
float scaleY = 1.0f;

const char* vertexShaderSource = R"(
#version 120

attribute vec2 aPos;

varying vec2 vPos;

uniform vec2 uScale;

void main()
{
    vec2 scaled = aPos * uScale;
    gl_Position = gl_ModelViewProjectionMatrix * vec4(scaled, 0.0, 1.0);
    vPos = aPos;
}
)";

const char* fragmentShaderSource = R"(
#version 120

varying vec2 vPos;

vec3 hsv2rgb(vec3 c)
{
    vec4 K = vec4(1.0, 2.0/3.0, 1.0/3.0, 3.0);
    vec3 p = abs(fract(c.xxx + K.xyz) * 6.0 - K.www);
    return c.z * mix(K.xxx, clamp(p - K.xxx, 0.0, 1.0), c.y);
}

void main()
{
    float r = length(vPos);
    if (r > 1.0)
        discard;

    float angle = atan(vPos.y, vPos.x);
    float h = angle / (6.28318530718) + 0.5;
    vec3 rgb = hsv2rgb(vec3(h, 1.0, 1.0));

    float t = clamp(r, 0.0, 1.0);
    vec3 finalColor = mix(vec3(1.0, 1.0, 1.0), rgb, t);

    gl_FragColor = vec4(finalColor, 1.0);
}
)";

GLuint compileShader(GLenum type, const char* source)
{
    GLuint shader = glCreateShader(type);
    glShaderSource(shader, 1, &source, 0);
    glCompileShader(shader);
    GLint status = 0;
    glGetShaderiv(shader, GL_COMPILE_STATUS, &status);
    if (!status)
    {
        GLint logLen = 0;
        glGetShaderiv(shader, GL_INFO_LOG_LENGTH, &logLen);
        if (logLen > 0)
        {
            std::string log(logLen, ' ');
            glGetShaderInfoLog(shader, logLen, 0, &log[0]);
            std::cerr << "Shader compile error: " << log << std::endl;
        }
        glDeleteShader(shader);
        return 0;
    }
    return shader;
}

GLuint createProgram(const char* vsSrc, const char* fsSrc)
{
    GLuint vs = compileShader(GL_VERTEX_SHADER, vsSrc);
    GLuint fs = compileShader(GL_FRAGMENT_SHADER, fsSrc);
    if (!vs || !fs)
        return 0;

    GLuint prog = glCreateProgram();
    glAttachShader(prog, vs);
    glAttachShader(prog, fs);

    glBindAttribLocation(prog, 0, "aPos");

    glLinkProgram(prog);

    GLint status = 0;
    glGetProgramiv(prog, GL_LINK_STATUS, &status);
    if (!status)
    {
        GLint logLen = 0;
        glGetProgramiv(prog, GL_INFO_LOG_LENGTH, &logLen);
        if (logLen > 0)
        {
            std::string log(logLen, ' ');
            glGetProgramInfoLog(prog, logLen, 0, &log[0]);
            std::cerr << "Program link error: " << log << std::endl;
        }
        glDeleteProgram(prog);
        return 0;
    }

    glDeleteShader(vs);
    glDeleteShader(fs);

    return prog;
}

void initShaders()
{
    shaderProgram = createProgram(vertexShaderSource, fragmentShaderSource);
    if (!shaderProgram)
    {
        std::cerr << "Failed to create shader program" << std::endl;
        std::exit(1);
    }

    glUseProgram(shaderProgram);
    uniformScaleLoc = glGetUniformLocation(shaderProgram, "uScale");
    glUniform2f(uniformScaleLoc, scaleX, scaleY);
}

void initVBO()
{
    const int segments = 128;
    std::vector<GLfloat> vertices;
    vertices.reserve((segments + 2) * 2);

    vertices.push_back(0.0f);
    vertices.push_back(0.0f);

    for (int i = 0; i <= segments; ++i)
    {
        float angle = (2.0f * 3.14159265359f * i) / segments;
        float x = std::cos(angle);
        float y = std::sin(angle);
        vertices.push_back(x);
        vertices.push_back(y);
    }

    glGenBuffers(1, &vbo);
    glBindBuffer(GL_ARRAY_BUFFER, vbo);
    glBufferData(GL_ARRAY_BUFFER, vertices.size() * sizeof(GLfloat), vertices.data(), GL_STATIC_DRAW);
    glBindBuffer(GL_ARRAY_BUFFER, 0);
}

void init()
{
    glClearColor(0.1f, 0.1f, 0.1f, 1.0f);
    glDisable(GL_DEPTH_TEST);

    initShaders();
    initVBO();
}

void display()
{
    glClear(GL_COLOR_BUFFER_BIT);

    glMatrixMode(GL_MODELVIEW);
    glLoadIdentity();

    glUseProgram(shaderProgram);
    glUniform2f(uniformScaleLoc, scaleX, scaleY);

    glBindBuffer(GL_ARRAY_BUFFER, vbo);
    glEnableVertexAttribArray(0);
    glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 2 * sizeof(GLfloat), (void*)0);

    glDrawArrays(GL_TRIANGLE_FAN, 0, 130);

    glDisableVertexAttribArray(0);
    glBindBuffer(GL_ARRAY_BUFFER, 0);

    glutSwapBuffers();
}

void reshape(int w, int h)
{
    if (h == 0) h = 1;
    float aspect = (float)w / (float)h;

    glViewport(0, 0, w, h);

    glMatrixMode(GL_PROJECTION);
    glLoadIdentity();

    if (aspect >= 1.0f)
        glOrtho(-aspect, aspect, -1.0, 1.0, -1.0, 1.0);
    else
        glOrtho(-1.0, 1.0, -1.0f / aspect, 1.0f / aspect, -1.0, 1.0);

    glMatrixMode(GL_MODELVIEW);
}

void keyboard(unsigned char key, int, int)
{
    switch (key)
    {
    case 27:
        std::exit(0);
    case '1':
        scaleX *= 1.1f;
        break;
    case '2':
        scaleX /= 1.1f;
        break;
    case '3':
        scaleY *= 1.1f;
        break;
    case '4':
        scaleY /= 1.1f;
        break;
    default:
        break;
    }

    glutPostRedisplay();
}

int main(int argc, char** argv)
{
    glutInit(&argc, argv);
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB);
    glutInitWindowSize(800, 600);
    glutCreateWindow("Gradient Circle HSV");

    GLenum err = glewInit();
    if (err != GLEW_OK)
    {
        std::cerr << "GLEW init error: " << glewGetErrorString(err) << std::endl;
        return 1;
    }

    init();

    glutDisplayFunc(display);
    glutReshapeFunc(reshape);
    glutKeyboardFunc(keyboard);

    glutMainLoop();
    return 0;
}
