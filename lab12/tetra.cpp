#include <GL/glew.h>
#include <GL/glut.h>
#include <iostream>

GLuint vbo = 0;
GLuint shaderProgram = 0;

GLint uniformOffsetLoc = -1;
GLint uniformAngleLoc = -1;

float tx = 0.0f;
float ty = 0.0f;
float tz = 0.0f;
float angleY = 0.0f;
float rotationSpeed = 0.2f;
bool rotating = false;

const char* vertexShaderSource = R"(
#version 120

attribute vec3 aPos;
attribute vec3 aColor;
attribute vec2 aTexCoord;

varying vec3 vColor;
varying vec2 vTexCoord;

uniform float uAngleY;
uniform vec3 uOffset;

void main()
{
    vec3 pos = aPos;

    float rad = uAngleY * 0.01745329251;
    float c = cos(rad);
    float s = sin(rad);
    mat3 rotY = mat3(
        c, 0.0, s,
        0.0, 1.0, 0.0,
        -s, 0.0, c
    );
    pos = rotY * pos;

    float radX = 0.43633232;
    float cx = cos(radX);
    float sx = sin(radX);
    mat3 rotX = mat3(
        1.0, 0.0, 0.0,
        0.0, cx, -sx,
        0.0, sx, cx
    );
    pos = rotX * pos;

    float radY0 = 0.61086524;
    float c0 = cos(radY0);
    float s0 = sin(radY0);
    mat3 rotY0 = mat3(
        c0, 0.0, s0,
        0.0, 1.0, 0.0,
        -s0, 0.0, c0
    );
    pos = rotY0 * pos;

    pos += uOffset;

    vec4 worldPos = vec4(pos, 1.0);
    gl_Position = gl_ModelViewProjectionMatrix * worldPos;

    vColor = aColor;
    vTexCoord = aTexCoord;
}
)";


const char* fragmentShaderSource = R"(
#version 120

varying vec3 vColor;
varying vec2 vTexCoord;

void main()
{
    gl_FragColor = vec4(vColor, 1.0);
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
    glBindAttribLocation(prog, 1, "aColor");
    glBindAttribLocation(prog, 2, "aTexCoord");

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
    uniformOffsetLoc = glGetUniformLocation(shaderProgram, "uOffset");
    uniformAngleLoc = glGetUniformLocation(shaderProgram, "uAngleY");
    glUniform3f(uniformOffsetLoc, tx, ty, tz);
    glUniform1f(uniformAngleLoc, angleY);
}

void initVBO()
{
    GLfloat vertices[] = {
         1.0f,  1.0f,  1.0f,   1.0f, 0.0f, 0.0f,   0.5f, 1.0f,
        -1.0f, -1.0f,  1.0f,   0.0f, 1.0f, 0.0f,   0.0f, 0.0f,
        -1.0f,  1.0f, -1.0f,   0.0f, 0.0f, 1.0f,   1.0f, 0.0f,

         1.0f,  1.0f,  1.0f,   1.0f, 0.0f, 0.0f,   0.5f, 1.0f,
        -1.0f, -1.0f,  1.0f,   0.0f, 1.0f, 0.0f,   0.0f, 0.0f,
         1.0f, -1.0f, -1.0f,   1.0f, 1.0f, 0.0f,   1.0f, 0.0f,

         1.0f,  1.0f,  1.0f,   1.0f, 0.0f, 0.0f,   0.5f, 1.0f,
        -1.0f,  1.0f, -1.0f,   0.0f, 0.0f, 1.0f,   0.0f, 0.0f,
         1.0f, -1.0f, -1.0f,   1.0f, 1.0f, 0.0f,   1.0f, 0.0f,

        -1.0f, -1.0f,  1.0f,   0.0f, 1.0f, 0.0f,   0.5f, 1.0f,
        -1.0f,  1.0f, -1.0f,   0.0f, 0.0f, 1.0f,   0.0f, 0.0f,
         1.0f, -1.0f, -1.0f,   1.0f, 1.0f, 0.0f,   1.0f, 0.0f
    };

    glGenBuffers(1, &vbo);
    glBindBuffer(GL_ARRAY_BUFFER, vbo);
    glBufferData(GL_ARRAY_BUFFER, sizeof(vertices), vertices, GL_STATIC_DRAW);
    glBindBuffer(GL_ARRAY_BUFFER, 0);
}

void init()
{
    glClearColor(0.1f, 0.1f, 0.1f, 1.0f);
    glEnable(GL_DEPTH_TEST);
    glShadeModel(GL_SMOOTH);
    initShaders();
    initVBO();
}

void display()
{
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);

    glMatrixMode(GL_MODELVIEW);
    glLoadIdentity();
    glTranslatef(0.0f, 0.0f, -5.0f);

    glUseProgram(shaderProgram);
    glUniform3f(uniformOffsetLoc, tx, ty, tz);
    glUniform1f(uniformAngleLoc, angleY);

    glBindBuffer(GL_ARRAY_BUFFER, vbo);

    glEnableVertexAttribArray(0);
    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 8 * sizeof(GLfloat), (void*)0);

    glEnableVertexAttribArray(1);
    glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 8 * sizeof(GLfloat), (void*)(3 * sizeof(GLfloat)));

    glEnableVertexAttribArray(2);
    glVertexAttribPointer(2, 2, GL_FLOAT, GL_FALSE, 8 * sizeof(GLfloat), (void*)(6 * sizeof(GLfloat)));

    glDrawArrays(GL_TRIANGLES, 0, 12);

    glDisableVertexAttribArray(0);
    glDisableVertexAttribArray(1);
    glDisableVertexAttribArray(2);

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
    gluPerspective(60.0, aspect, 0.1, 100.0);
    glMatrixMode(GL_MODELVIEW);
}

void idle()
{
    if (rotating)
    {
        angleY += rotationSpeed;
        if (angleY > 360.0f)
            angleY -= 360.0f;
        glutPostRedisplay();
    }
}

void keyboard(unsigned char key, int, int)
{
    float step = 0.1f;

    switch (key)
    {
    case 27:
        std::exit(0);
    case 'a':
    case 'A':
        tx -= step;
        break;
    case 'd':
    case 'D':
        tx += step;
        break;
    case 'w':
    case 'W':
        ty += step;
        break;
    case 's':
    case 'S':
        ty -= step;
        break;
    case 'q':
    case 'Q':
        tz += step;
        break;
    case 'e':
    case 'E':
        tz -= step;
        break;
    case ' ':
        rotating = !rotating;
        break;
    case 'z':
    case 'Z':
        rotationSpeed -= 0.05f;
        if (rotationSpeed < 0.0f)
            rotationSpeed = 0.0f;
        break;
    case 'x':
    case 'X':
        rotationSpeed += 0.05f;
        break;
    default:
        break;
    }

    glutPostRedisplay();
}

int main(int argc, char** argv)
{
    glutInit(&argc, argv);
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH);
    glutInitWindowSize(800, 600);
    glutCreateWindow("Gradient Tetrahedron VBO + Shaders");

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
    glutIdleFunc(idle);

    glutMainLoop();
    return 0;
}
