#include <GL/glew.h>
#include <SFML/Window.hpp>
#include <SFML/OpenGL.hpp>

#include <iostream>
#include <vector>
#include <cmath>

GLuint Program;
GLint  Attrib_vertex;
GLuint VBO_quad;
GLuint VBO_fan;
GLuint VBO_pentagon;

struct Vertex {
    GLfloat x;
    GLfloat y;
};

const int QUAD_VERTEX_COUNT = 6;
const int FAN_OUTER_COUNT = 6;
const int FAN_VERTEX_COUNT = FAN_OUTER_COUNT + 1;
const int PENTAGON_VERTEX_COUNT = 7;

const char* VertexShaderSource = R"(
    #version 330 core
    in vec2 coord;
    void main() {
        gl_Position = vec4(coord, 0.0, 1.0);
    }
)";

const char* FragShaderSource = R"(
    #version 330 core
    out vec4 color;
    void main() {
        color = vec4(0, 1, 0, 1);
    }
)";

void Init();
void InitVBO();
void InitShader();
void Draw();
void Release();
void ReleaseShader();
void ReleaseVBO();

void ShaderLog(GLuint shader);
void checkOpenGLerror();

int main() {
    sf::Window window(
        sf::VideoMode(600, 600),
        "lab figures",
        sf::Style::Default,
        sf::ContextSettings(24)
    );

    window.setVerticalSyncEnabled(true);
    window.setActive(true);

    GLenum glew_status = glewInit();
    if (glew_status != GLEW_OK) {
        std::cerr << "GLEW error: " << glewGetErrorString(glew_status) << std::endl;
        return 1;
    }

    glClearColor(0.f, 0.f, 0.f, 1.f);

    Init();

    while (window.isOpen()) {
        sf::Event event;
        while (window.pollEvent(event)) {
            if (event.type == sf::Event::Closed) {
                window.close();
            } else if (event.type == sf::Event::Resized) {
                glViewport(0, 0, event.size.width, event.size.height);
            } else if (event.type == sf::Event::KeyPressed &&
                       event.key.code == sf::Keyboard::Escape) {
                window.close();
            }
        }

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);

        Draw();

        window.display();
    }

    Release();

    return 0;
}

void Init() {
    InitShader();
    InitVBO();
}

void InitVBO() {
    glGenBuffers(1, &VBO_quad);
    Vertex quad[QUAD_VERTEX_COUNT] = {
        { -0.95f, -0.4f },
        { -0.55f, -0.4f },
        { -0.95f,  0.2f },
        { -0.55f, -0.4f },
        { -0.55f,  0.2f },
        { -0.95f,  0.2f }
    };
    glBindBuffer(GL_ARRAY_BUFFER, VBO_quad);
    glBufferData(GL_ARRAY_BUFFER, sizeof(quad), quad, GL_STATIC_DRAW);

    glGenBuffers(1, &VBO_fan);
    Vertex fan[FAN_VERTEX_COUNT];
    const float PI = 3.1415926535f;
    float cx = 0.0f;
    float cy = -0.5f;
    float r = 0.35f;
    fan[0].x = cx;
    fan[0].y = cy;
    float startAngle = -PI / 3.0f;
    float endAngle   =  PI / 3.0f;
    for (int i = 0; i < FAN_OUTER_COUNT; ++i) {
        float t = static_cast<float>(i) / static_cast<float>(FAN_OUTER_COUNT - 1);
        float angle = startAngle + (endAngle - startAngle) * t;
        fan[i + 1].x = cx + r * std::cos(angle);
        fan[i + 1].y = cy + r * std::sin(angle);
    }
    glBindBuffer(GL_ARRAY_BUFFER, VBO_fan);
    glBufferData(GL_ARRAY_BUFFER, sizeof(fan), fan, GL_STATIC_DRAW);

    glGenBuffers(1, &VBO_pentagon);
    Vertex pentagon[PENTAGON_VERTEX_COUNT];
    pentagon[0].x = 0.75f;
    pentagon[0].y = 0.35f;
    float rp = 0.2f;
    for (int i = 0; i < 5; ++i) {
        float angle = 2.f * PI * i / 5.f - PI / 2.f;
        pentagon[i + 1].x = pentagon[0].x + rp * std::cos(angle);
        pentagon[i + 1].y = pentagon[0].y + rp * std::sin(angle);
    }
    pentagon[6] = pentagon[1];
    glBindBuffer(GL_ARRAY_BUFFER, VBO_pentagon);
    glBufferData(GL_ARRAY_BUFFER, sizeof(pentagon), pentagon, GL_STATIC_DRAW);

    glBindBuffer(GL_ARRAY_BUFFER, 0);

    checkOpenGLerror();
}


void InitShader() {
    GLuint vShader = glCreateShader(GL_VERTEX_SHADER);
    glShaderSource(vShader, 1, &VertexShaderSource, nullptr);
    glCompileShader(vShader);
    ShaderLog(vShader);

    GLuint fShader = glCreateShader(GL_FRAGMENT_SHADER);
    glShaderSource(fShader, 1, &FragShaderSource, nullptr);
    glCompileShader(fShader);
    ShaderLog(fShader);

    Program = glCreateProgram();
    glAttachShader(Program, vShader);
    glAttachShader(Program, fShader);
    glLinkProgram(Program);

    GLint link_ok = GL_FALSE;
    glGetProgramiv(Program, GL_LINK_STATUS, &link_ok);
    if (!link_ok) {
        std::cout << "error attach shaders\n";
        return;
    }

    glDeleteShader(vShader);
    glDeleteShader(fShader);

    const char* attr_name = "coord";
    Attrib_vertex = glGetAttribLocation(Program, attr_name);
    if (Attrib_vertex == -1) {
        std::cout << "could not bind attrib " << attr_name << std::endl;
        return;
    }

    checkOpenGLerror();
}

void Draw() {
    glUseProgram(Program);
    glEnableVertexAttribArray(Attrib_vertex);

    glBindBuffer(GL_ARRAY_BUFFER, VBO_quad);
    glVertexAttribPointer(Attrib_vertex, 2, GL_FLOAT, GL_FALSE, 0, (void*)0);
    glDrawArrays(GL_TRIANGLES, 0, QUAD_VERTEX_COUNT);

    glBindBuffer(GL_ARRAY_BUFFER, VBO_fan);
    glVertexAttribPointer(Attrib_vertex, 2, GL_FLOAT, GL_FALSE, 0, (void*)0);
    glDrawArrays(GL_TRIANGLE_FAN, 0, FAN_VERTEX_COUNT);

    glBindBuffer(GL_ARRAY_BUFFER, VBO_pentagon);
    glVertexAttribPointer(Attrib_vertex, 2, GL_FLOAT, GL_FALSE, 0, (void*)0);
    glDrawArrays(GL_TRIANGLE_FAN, 0, PENTAGON_VERTEX_COUNT);

    glBindBuffer(GL_ARRAY_BUFFER, 0);

    glDisableVertexAttribArray(Attrib_vertex);
    glUseProgram(0);

    checkOpenGLerror();
}

void Release() {
    ReleaseShader();
    ReleaseVBO();
}

void ReleaseShader() {
    glUseProgram(0);
    if (Program != 0) {
        glDeleteProgram(Program);
        Program = 0;
    }
}

void ReleaseVBO() {
    glBindBuffer(GL_ARRAY_BUFFER, 0);
    if (VBO_quad != 0) {
        glDeleteBuffers(1, &VBO_quad);
        VBO_quad = 0;
    }
    if (VBO_fan != 0) {
        glDeleteBuffers(1, &VBO_fan);
        VBO_fan = 0;
    }
    if (VBO_pentagon != 0) {
        glDeleteBuffers(1, &VBO_pentagon);
        VBO_pentagon = 0;
    }
}

void ShaderLog(GLuint shader) {
    GLint infologLen = 0;
    glGetShaderiv(shader, GL_INFO_LOG_LENGTH, &infologLen);
    if (infologLen > 1) {
        GLint charsWritten = 0;
        std::vector<char> infoLog(infologLen);
        glGetShaderInfoLog(shader, infologLen, &charsWritten, infoLog.data());
        std::cout << "InfoLog: " << infoLog.data() << std::endl;
    }
}

void checkOpenGLerror() {
    bool wasError = false;
    GLenum err;
    while ((err = glGetError()) != GL_NO_ERROR) {
        wasError = true;
        std::cout << "OpenGL error: " << err << std::endl;
    }
    if (wasError) {
        std::cout << std::endl;
    }
}
