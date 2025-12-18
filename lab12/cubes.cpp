#include <GL/glew.h>
#include <GL/glut.h>
#include <iostream>
#include <string>
#include <cmath>

#define STB_IMAGE_IMPLEMENTATION
#include "stb_image.h"

GLuint vbo = 0;
GLuint shaderProgram = 0;
GLuint tex1Id = 0;
GLuint tex2Id = 0;

GLint uniformAngleLoc = -1;
GLint uniformGlobalOffsetLoc = -1;
GLint uniformCubeOffsetLoc = -1;
GLint uniformColorFactorLoc = -1;
GLint uniformTextureMixLoc = -1;
GLint uniformTex1Loc = -1;
GLint uniformTex2Loc = -1;

float angleY = 0.0f;
float rotationSpeed = 0.8f;
bool rotating = true;

float globalTx = 0.0f;
float globalTy = 0.0f;

float colorFactor = 0.5f;
float textureMixFactor = 0.5f;

const char* vertexShaderSource = R"(
#version 120

attribute vec3 aPos;
attribute vec3 aColor;
attribute vec2 aTexCoord;

varying vec3 vColor;
varying vec2 vTexCoord;

uniform float uAngleY;
uniform vec3 uGlobalOffset;
uniform vec3 uCubeOffset;

void main()
{
    vec3 pos = aPos;

    float radX = 0.6;
    float cx = cos(radX);
    float sx = sin(radX);
    mat3 rotX = mat3(
        1.0, 0.0, 0.0,
        0.0, cx, -sx,
        0.0, sx, cx
    );
    pos = rotX * pos;

    float radY = uAngleY * 0.01745329251;
    float cy = cos(radY);
    float sy = sin(radY);
    mat3 rotY = mat3(
        cy, 0.0, sy,
        0.0, 1.0, 0.0,
        -sy, 0.0, cy
    );
    pos = rotY * pos;

    pos += uCubeOffset + uGlobalOffset;

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

uniform sampler2D uTex1;
uniform sampler2D uTex2;
uniform float uColorFactor;
uniform float uTextureMixFactor;

void main()
{
    vec4 t1 = texture2D(uTex1, vTexCoord);
    vec4 t2 = texture2D(uTex2, vTexCoord);
    vec4 texMixed = mix(t1, t2, clamp(uTextureMixFactor, 0.0, 1.0));
    vec4 colorMixed = mix(texMixed, vec4(vColor, 1.0), clamp(uColorFactor, 0.0, 1.0));
    gl_FragColor = colorMixed;
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

GLuint loadTexture(const char* filename)
{
    int width, height, channels;
    unsigned char* data = stbi_load(filename, &width, &height, &channels, 0);
    if (!data)
    {
        std::cerr << "Failed to load texture: " << filename << std::endl;
        return 0;
    }

    GLenum format = GL_RGB;
    if (channels == 1)
        format = GL_LUMINANCE;
    else if (channels == 3)
        format = GL_RGB;
    else if (channels == 4)
        format = GL_RGBA;

    GLuint texId;
    glGenTextures(1, &texId);
    glBindTexture(GL_TEXTURE_2D, texId);
    glTexImage2D(GL_TEXTURE_2D, 0, format, width, height, 0, format, GL_UNSIGNED_BYTE, data);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT);
    glBindTexture(GL_TEXTURE_2D, 0);

    stbi_image_free(data);
    return texId;
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

    uniformAngleLoc = glGetUniformLocation(shaderProgram, "uAngleY");
    uniformGlobalOffsetLoc = glGetUniformLocation(shaderProgram, "uGlobalOffset");
    uniformCubeOffsetLoc = glGetUniformLocation(shaderProgram, "uCubeOffset");
    uniformColorFactorLoc = glGetUniformLocation(shaderProgram, "uColorFactor");
    uniformTextureMixLoc = glGetUniformLocation(shaderProgram, "uTextureMixFactor");
    uniformTex1Loc = glGetUniformLocation(shaderProgram, "uTex1");
    uniformTex2Loc = glGetUniformLocation(shaderProgram, "uTex2");

    glUniform1i(uniformTex1Loc, 0);
    glUniform1i(uniformTex2Loc, 1);
}

void initVBO()
{
    GLfloat vertices[] = {
        -1.0f,-1.0f, 1.0f,  1.0f,0.0f,0.0f,  0.0f,0.0f,
         1.0f,-1.0f, 1.0f,  1.0f,0.0f,0.0f,  1.0f,0.0f,
         1.0f, 1.0f, 1.0f,  1.0f,0.0f,0.0f,  1.0f,1.0f,
        -1.0f,-1.0f, 1.0f,  1.0f,0.0f,0.0f,  0.0f,0.0f,
         1.0f, 1.0f, 1.0f,  1.0f,0.0f,0.0f,  1.0f,1.0f,
        -1.0f, 1.0f, 1.0f,  1.0f,0.0f,0.0f,  0.0f,1.0f,

        -1.0f,-1.0f,-1.0f,  0.0f,1.0f,0.0f,  1.0f,0.0f,
        -1.0f, 1.0f,-1.0f,  0.0f,1.0f,0.0f,  1.0f,1.0f,
         1.0f, 1.0f,-1.0f,  0.0f,1.0f,0.0f,  0.0f,1.0f,
        -1.0f,-1.0f,-1.0f,  0.0f,1.0f,0.0f,  1.0f,0.0f,
         1.0f, 1.0f,-1.0f,  0.0f,1.0f,0.0f,  0.0f,1.0f,
         1.0f,-1.0f,-1.0f,  0.0f,1.0f,0.0f,  0.0f,0.0f,

        -1.0f,-1.0f,-1.0f,  0.0f,0.0f,1.0f,  0.0f,0.0f,
        -1.0f,-1.0f, 1.0f,  0.0f,0.0f,1.0f,  1.0f,0.0f,
        -1.0f, 1.0f, 1.0f,  0.0f,0.0f,1.0f,  1.0f,1.0f,
        -1.0f,-1.0f,-1.0f,  0.0f,0.0f,1.0f,  0.0f,0.0f,
        -1.0f, 1.0f, 1.0f,  0.0f,0.0f,1.0f,  1.0f,1.0f,
        -1.0f, 1.0f,-1.0f,  0.0f,0.0f,1.0f,  0.0f,1.0f,

         1.0f,-1.0f,-1.0f,  1.0f,1.0f,0.0f,  1.0f,0.0f,
         1.0f, 1.0f,-1.0f,  1.0f,1.0f,0.0f,  1.0f,1.0f,
         1.0f, 1.0f, 1.0f,  1.0f,1.0f,0.0f,  0.0f,1.0f,
         1.0f,-1.0f,-1.0f,  1.0f,1.0f,0.0f,  1.0f,0.0f,
         1.0f, 1.0f, 1.0f,  1.0f,1.0f,0.0f,  0.0f,1.0f,
         1.0f,-1.0f, 1.0f,  1.0f,1.0f,0.0f,  0.0f,0.0f,

        -1.0f, 1.0f, 1.0f,  1.0f,0.0f,1.0f,  0.0f,1.0f,
         1.0f, 1.0f, 1.0f,  1.0f,0.0f,1.0f,  1.0f,1.0f,
         1.0f, 1.0f,-1.0f,  1.0f,0.0f,1.0f,  1.0f,0.0f,
        -1.0f, 1.0f, 1.0f,  1.0f,0.0f,1.0f,  0.0f,1.0f,
         1.0f, 1.0f,-1.0f,  1.0f,0.0f,1.0f,  1.0f,0.0f,
        -1.0f, 1.0f,-1.0f,  1.0f,0.0f,1.0f,  0.0f,0.0f,

        -1.0f,-1.0f, 1.0f,  0.0f,1.0f,1.0f,  0.0f,0.0f,
        -1.0f,-1.0f,-1.0f,  0.0f,1.0f,1.0f,  0.0f,1.0f,
         1.0f,-1.0f,-1.0f,  0.0f,1.0f,1.0f,  1.0f,1.0f,
        -1.0f,-1.0f, 1.0f,  0.0f,1.0f,1.0f,  0.0f,0.0f,
         1.0f,-1.0f,-1.0f,  0.0f,1.0f,1.0f,  1.0f,1.0f,
         1.0f,-1.0f, 1.0f,  0.0f,1.0f,1.0f,  1.0f,0.0f
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
    glEnable(GL_TEXTURE_2D);

    initShaders();
    initVBO();

    tex1Id = loadTexture("1.png");
    tex2Id = loadTexture("2.png");
    if (!tex1Id || !tex2Id)
    {
        std::cerr << "Failed to load textures 1.png or 2.png" << std::endl;
        std::exit(1);
    }
}

void display()
{
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);

    glMatrixMode(GL_MODELVIEW);
    glLoadIdentity();
    glTranslatef(0.0f, 0.0f, -7.0f);

    glUseProgram(shaderProgram);

    glActiveTexture(GL_TEXTURE0);
    glBindTexture(GL_TEXTURE_2D, tex1Id);
    glActiveTexture(GL_TEXTURE1);
    glBindTexture(GL_TEXTURE_2D, tex2Id);

    glUniform1f(uniformAngleLoc, angleY);
    glUniform3f(uniformGlobalOffsetLoc, globalTx, globalTy, 0.0f);

    glBindBuffer(GL_ARRAY_BUFFER, vbo);

    glEnableVertexAttribArray(0);
    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 8 * sizeof(GLfloat), (void*)0);

    glEnableVertexAttribArray(1);
    glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 8 * sizeof(GLfloat), (void*)(3 * sizeof(GLfloat)));

    glEnableVertexAttribArray(2);
    glVertexAttribPointer(2, 2, GL_FLOAT, GL_FALSE, 8 * sizeof(GLfloat), (void*)(6 * sizeof(GLfloat)));

    glUniform3f(uniformCubeOffsetLoc, -2.2f, 0.0f, 0.0f);
    glUniform1f(uniformColorFactorLoc, colorFactor);
    glUniform1f(uniformTextureMixLoc, 0.0f);
    glDrawArrays(GL_TRIANGLES, 0, 36);

    glUniform3f(uniformCubeOffsetLoc, 2.2f, 0.0f, 0.0f);
    glUniform1f(uniformColorFactorLoc, 0.0f);
    glUniform1f(uniformTextureMixLoc, textureMixFactor);
    glDrawArrays(GL_TRIANGLES, 0, 36);

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
    case ' ':
        rotating = !rotating;
        break;
    case 'w':
    case 'W':
        globalTy += step;
        break;
    case 's':
    case 'S':
        globalTy -= step;
        break;
    case 'a':
    case 'A':
        globalTx -= step;
        break;
    case 'd':
    case 'D':
        globalTx += step;
        break;
    case 'z':
    case 'Z':
        rotationSpeed -= 0.1f;
        if (rotationSpeed < 0.0f) rotationSpeed = 0.0f;
        break;
    case 'x':
    case 'X':
        rotationSpeed += 0.1f;
        break;
    case '1':
        colorFactor -= 0.05f;
        if (colorFactor < 0.0f) colorFactor = 0.0f;
        break;
    case '2':
        colorFactor += 0.05f;
        if (colorFactor > 1.0f) colorFactor = 1.0f;
        break;
    case '3':
        textureMixFactor -= 0.05f;
        if (textureMixFactor < 0.0f) textureMixFactor = 0.0f;
        break;
    case '4':
        textureMixFactor += 0.05f;
        if (textureMixFactor > 1.0f) textureMixFactor = 1.0f;
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
    glutInitWindowSize(900, 600);
    glutCreateWindow("Textured Cubes");

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
