#define STB_IMAGE_IMPLEMENTATION
#include <iostream>
#include <vector>
#include <string>
#include <fstream>
#include <sstream>
#include <memory>
#include <cmath>
#include <algorithm>
#include "stb_image.h"

#include <GL/glew.h>
#include <SFML/Window.hpp>
#include <SFML/OpenGL.hpp>

struct Vec3{float x,y,z;Vec3():x(0),y(0),z(0){}Vec3(float x,float y,float z):x(x),y(y),z(z){}Vec3 operator+(const Vec3&o)const{return Vec3(x+o.x,y+o.y,z+o.z);}Vec3 operator-(const Vec3&o)const{return Vec3(x-o.x,y-o.y,z-o.z);}Vec3 operator*(float s)const{return Vec3(x*s,y*s,z*s);}Vec3 operator/(float s)const{return Vec3(x/s,y/s,z/s);}float length()const{return std::sqrt(x*x+y*y+z*z);}Vec3 normalize()const{float l=length();return(l>0.0f)?(*this/l):*this;}float dot(const Vec3&o)const{return x*o.x+y*o.y+z*o.z;}Vec3 cross(const Vec3&o)const{return Vec3(y*o.z-z*o.y,z*o.x-x*o.z,x*o.y-y*o.x);}};
struct Vec2{float x,y;Vec2():x(0),y(0){}Vec2(float x,float y):x(x),y(y){}};

struct Mat4{
    float m[16];
    Mat4(){for(int i=0;i<16;i++)m[i]=0.0f;m[0]=m[5]=m[10]=m[15]=1.0f;}
    static Mat4 identity(){return Mat4();}
    static Mat4 translate(float x,float y,float z){Mat4 r=identity();r.m[12]=x;r.m[13]=y;r.m[14]=z;return r;}
    static Mat4 translate(const Vec3&v){return translate(v.x,v.y,v.z);}
    static Mat4 scale(float x,float y,float z){Mat4 r=identity();r.m[0]=x;r.m[5]=y;r.m[10]=z;return r;}
    static Mat4 scale(const Vec3&v){return scale(v.x,v.y,v.z);}
    static Mat4 rotate(float angle,const Vec3&axis){
        Mat4 r=identity();
        float c=std::cos(angle),s=std::sin(angle),t=1.0f-c;
        Vec3 a=axis.normalize();float x=a.x,y=a.y,z=a.z;
        r.m[0]=t*x*x+c;      r.m[1]=t*x*y+s*z;  r.m[2]=t*x*z-s*y;
        r.m[4]=t*x*y-s*z;    r.m[5]=t*y*y+c;    r.m[6]=t*y*z+s*x;
        r.m[8]=t*x*z+s*y;    r.m[9]=t*y*z-s*x;  r.m[10]=t*z*z+c;
        return r;
    }
    static Mat4 perspective(float fov,float aspect,float nearZ,float farZ){
        Mat4 r;float f=1.0f/std::tan(fov*0.5f*3.14159265359f/180.0f);
        r.m[0]=f/aspect;r.m[5]=f;r.m[10]=(farZ+nearZ)/(nearZ-farZ);r.m[11]=-1.0f;r.m[14]=(2.0f*farZ*nearZ)/(nearZ-farZ);r.m[15]=0.0f;
        return r;
    }
    static Mat4 lookAt(const Vec3&eye,const Vec3&center,const Vec3&up){
        Vec3 f=(center-eye).normalize();
        Vec3 s=f.cross(up.normalize()).normalize();
        Vec3 u=s.cross(f);
        Mat4 r=identity();
        r.m[0]=s.x;r.m[4]=s.y;r.m[8]=s.z;
        r.m[1]=u.x;r.m[5]=u.y;r.m[9]=u.z;
        r.m[2]=-f.x;r.m[6]=-f.y;r.m[10]=-f.z;
        r.m[12]=-s.dot(eye);r.m[13]=-u.dot(eye);r.m[14]=f.dot(eye);
        return r;
    }
    Mat4 operator*(const Mat4&o)const{
        Mat4 r;
        for(int c=0;c<4;c++)for(int row=0;row<4;row++)
            r.m[c*4+row]=m[0*4+row]*o.m[c*4+0]+m[1*4+row]*o.m[c*4+1]+m[2*4+row]*o.m[c*4+2]+m[3*4+row]*o.m[c*4+3];
        return r;
    }
};

struct Vertex{Vec3 position;Vec3 normal;Vec2 texcoord;Vertex():position(),normal(0,1,0),texcoord(0,0){}Vertex(const Vec3&p,const Vec3&n,const Vec2&t):position(p),normal(n),texcoord(t){}};

static GLuint loadTexture2D(const std::string& filename){
    int w=0,h=0,ch=0;
    stbi_set_flip_vertically_on_load(true);
    unsigned char* data=stbi_load(filename.c_str(),&w,&h,&ch,0);
    if(!data){std::cerr<<"Failed to load texture: "<<filename<<std::endl;return 0;}
    GLenum format=GL_RGB;
    if(ch==1)format=GL_RED;
    else if(ch==3)format=GL_RGB;
    else if(ch==4)format=GL_RGBA;
    GLuint tex=0;
    glGenTextures(1,&tex);
    glBindTexture(GL_TEXTURE_2D,tex);
    glPixelStorei(GL_UNPACK_ALIGNMENT,1);
    glTexImage2D(GL_TEXTURE_2D,0,format,w,h,0,format,GL_UNSIGNED_BYTE,data);
    glGenerateMipmap(GL_TEXTURE_2D);
    glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_WRAP_S,GL_REPEAT);
    glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_WRAP_T,GL_REPEAT);
    glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MIN_FILTER,GL_LINEAR_MIPMAP_LINEAR);
    glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MAG_FILTER,GL_LINEAR);
    glBindTexture(GL_TEXTURE_2D,0);
    stbi_image_free(data);
    return tex;
}

static std::string pickTextureFile(const std::string& baseName){
    std::vector<std::string> exts={".png",".jpg",".jpeg",".bmp",".tga"};
    for(const auto& e:exts){
        std::ifstream f(baseName+e);
        if(f.good()) return baseName+e;
    }
    return "";
}

class Mesh{
private:
    GLuint vao,vbo,ebo;
    std::vector<Vertex> vertices;
    std::vector<unsigned int> indices;
    bool ready;
public:
    Mesh():vao(0),vbo(0),ebo(0),ready(false){}
    ~Mesh(){if(vao)glDeleteVertexArrays(1,&vao);if(vbo)glDeleteBuffers(1,&vbo);if(ebo)glDeleteBuffers(1,&ebo);}
    bool loadFromObj(const std::string& filename){
        std::ifstream file(filename);
        if(!file.is_open()){std::cerr<<"Не удалось открыть OBJ: "<<filename<<std::endl;return false;}

        std::vector<Vec3> tempPositions;
        std::vector<Vec3> tempNormals;
        std::vector<Vec2> tempTexcoords;
        vertices.clear();
        indices.clear();

        std::string line;
        while(std::getline(file,line)){
            if(line.empty()) continue;
            std::istringstream iss(line);
            std::string prefix;
            iss>>prefix;
            if(prefix=="v"){
                Vec3 p;iss>>p.x>>p.y>>p.z;tempPositions.push_back(p);
            }else if(prefix=="vn"){
                Vec3 n;iss>>n.x>>n.y>>n.z;tempNormals.push_back(n);
            }else if(prefix=="vt"){
                Vec2 t;iss>>t.x>>t.y;tempTexcoords.push_back(t);
            }else if(prefix=="f"){
                std::string v[4];iss>>v[0]>>v[1]>>v[2]>>v[3];
                int faceCount=v[3].empty()?3:4;
                int triIndexOrder[6]={0,1,2,0,2,3};
                for(int k=0;k<(faceCount==3?3:6);k++){
                    const std::string& vertexStr=v[triIndexOrder[k]];
                    std::istringstream viss(vertexStr);
                    std::string token;
                    std::vector<std::string> parts;
                    while(std::getline(viss,token,'/')) parts.push_back(token);

                    Vertex vert;
                    if(!parts.empty() && !parts[0].empty()){
                        int idx=std::stoi(parts[0]); if(idx<0) idx=(int)tempPositions.size()+idx+1; idx-=1;
                        if(idx>=0 && idx<(int)tempPositions.size()) vert.position=tempPositions[idx];
                    }
                    if(parts.size()>1 && !parts[1].empty()){
                        int idx=std::stoi(parts[1]); if(idx<0) idx=(int)tempTexcoords.size()+idx+1; idx-=1;
                        if(idx>=0 && idx<(int)tempTexcoords.size()) vert.texcoord=tempTexcoords[idx];
                    }else{
                        vert.texcoord=Vec2(0.0f,0.0f);
                    }
                    if(parts.size()>2 && !parts[2].empty()){
                        int idx=std::stoi(parts[2]); if(idx<0) idx=(int)tempNormals.size()+idx+1; idx-=1;
                        if(idx>=0 && idx<(int)tempNormals.size()) vert.normal=tempNormals[idx];
                    }else{
                        vert.normal=Vec3(0.0f,1.0f,0.0f);
                    }

                    vertices.push_back(vert);
                    indices.push_back((unsigned int)vertices.size()-1);
                }
            }
        }

        if(vertices.empty() || indices.empty()){
            std::cerr<<"OBJ пустой или без граней: "<<filename<<std::endl;
            return false;
        }
        if(tempNormals.empty()) computeNormals();
        if(tempTexcoords.empty()) generatePlanarUVs();

        setupBuffers();
        ready=true;
        if(indices.size()/3 < 100) std::cerr<<"Warning: "<<filename<<" has "<<(indices.size()/3)<<" triangles (<100)"<<std::endl;
        return true;
    }

    void draw() const{
        if(!ready) return;
        glBindVertexArray(vao);
        glDrawElements(GL_TRIANGLES,(GLsizei)indices.size(),GL_UNSIGNED_INT,nullptr);
        glBindVertexArray(0);
    }

private:
    void setupBuffers(){
        if(vao)glDeleteVertexArrays(1,&vao);
        if(vbo)glDeleteBuffers(1,&vbo);
        if(ebo)glDeleteBuffers(1,&ebo);

        glGenVertexArrays(1,&vao);
        glGenBuffers(1,&vbo);
        glGenBuffers(1,&ebo);

        glBindVertexArray(vao);

        glBindBuffer(GL_ARRAY_BUFFER,vbo);
        glBufferData(GL_ARRAY_BUFFER,vertices.size()*sizeof(Vertex),vertices.data(),GL_STATIC_DRAW);

        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER,ebo);
        glBufferData(GL_ELEMENT_ARRAY_BUFFER,indices.size()*sizeof(unsigned int),indices.data(),GL_STATIC_DRAW);

        glVertexAttribPointer(0,3,GL_FLOAT,GL_FALSE,sizeof(Vertex),(void*)offsetof(Vertex,position));
        glEnableVertexAttribArray(0);
        glVertexAttribPointer(1,3,GL_FLOAT,GL_FALSE,sizeof(Vertex),(void*)offsetof(Vertex,normal));
        glEnableVertexAttribArray(1);
        glVertexAttribPointer(2,2,GL_FLOAT,GL_FALSE,sizeof(Vertex),(void*)offsetof(Vertex,texcoord));
        glEnableVertexAttribArray(2);

        glBindVertexArray(0);
    }

    void computeNormals(){
        for(auto& v:vertices) v.normal=Vec3(0,0,0);
        for(size_t i=0;i+2<indices.size();i+=3){
            Vertex& v0=vertices[indices[i]];
            Vertex& v1=vertices[indices[i+1]];
            Vertex& v2=vertices[indices[i+2]];
            Vec3 e1=v1.position-v0.position;
            Vec3 e2=v2.position-v0.position;
            Vec3 n=e1.cross(e2).normalize();
            v0.normal=v0.normal+n;
            v1.normal=v1.normal+n;
            v2.normal=v2.normal+n;
        }
        for(auto& v:vertices) v.normal=v.normal.normalize();
    }

    void generatePlanarUVs(){
        Vec3 minP(1e9f,1e9f,1e9f),maxP(-1e9f,-1e9f,-1e9f);
        for(const auto& v:vertices){
            minP.x=std::min(minP.x,v.position.x);
            minP.y=std::min(minP.y,v.position.y);
            minP.z=std::min(minP.z,v.position.z);
            maxP.x=std::max(maxP.x,v.position.x);
            maxP.y=std::max(maxP.y,v.position.y);
            maxP.z=std::max(maxP.z,v.position.z);
        }
        Vec3 size=maxP-minP;
        float sx=(std::abs(size.x)<1e-6f)?1.0f:size.x;
        float sz=(std::abs(size.z)<1e-6f)?1.0f:size.z;
        for(auto& v:vertices){
            float u=(v.position.x-minP.x)/sx;
            float t=(v.position.z-minP.z)/sz;
            v.texcoord=Vec2(u,t);
        }
    }
};

class Shader{
private:
    GLuint programId;
public:
    Shader():programId(0){}
    ~Shader(){if(programId)glDeleteProgram(programId);}
    bool compile(const std::string& vs, const std::string& fs){
        const char* vCode=vs.c_str();
        const char* fCode=fs.c_str();
        GLuint v=glCreateShader(GL_VERTEX_SHADER);
        glShaderSource(v,1,&vCode,nullptr);
        glCompileShader(v);
        if(!check(v,false)) return false;
        GLuint f=glCreateShader(GL_FRAGMENT_SHADER);
        glShaderSource(f,1,&fCode,nullptr);
        glCompileShader(f);
        if(!check(f,false)) return false;
        programId=glCreateProgram();
        glAttachShader(programId,v);
        glAttachShader(programId,f);
        glLinkProgram(programId);
        glDeleteShader(v);
        glDeleteShader(f);
        return check(programId,true);
    }
    void use()const{glUseProgram(programId);}
    GLuint id()const{return programId;}
    void setMat4(const std::string& name,const Mat4& mat)const{GLint loc=glGetUniformLocation(programId,name.c_str());if(loc!=-1)glUniformMatrix4fv(loc,1,GL_FALSE,mat.m);}
    void setVec3(const std::string& name,const Vec3& v)const{GLint loc=glGetUniformLocation(programId,name.c_str());if(loc!=-1)glUniform3f(loc,v.x,v.y,v.z);}
    void setInt(const std::string& name,int v)const{GLint loc=glGetUniformLocation(programId,name.c_str());if(loc!=-1)glUniform1i(loc,v);}
private:
    bool check(GLuint obj,bool isProgram){
        GLint ok=0;char info[1024];
        if(!isProgram){
            glGetShaderiv(obj,GL_COMPILE_STATUS,&ok);
            if(!ok){glGetShaderInfoLog(obj,1024,nullptr,info);std::cerr<<info<<std::endl;return false;}
        }else{
            glGetProgramiv(obj,GL_LINK_STATUS,&ok);
            if(!ok){glGetProgramInfoLog(obj,1024,nullptr,info);std::cerr<<info<<std::endl;return false;}
        }
        return true;
    }
};

class Camera{
public:
    Vec3 position,front,up,right,worldUp;
    float yaw,pitch,speed,sensitivity,fov;
    Camera(const Vec3& pos=Vec3(0.0f,3.0f,18.0f)):position(pos),worldUp(0,1,0),yaw(-90.0f),pitch(-10.0f),speed(8.0f),sensitivity(0.1f),fov(45.0f){updateVectors();}
    Mat4 view()const{return Mat4::lookAt(position,position+front,up);}
    void processKeyboard(int dir,float dt){
        float v=speed*dt;
        if(dir==0) position=position+front*v;
        if(dir==1) position=position-front*v;
        if(dir==2) position=position-right*v;
        if(dir==3) position=position+right*v;
        if(dir==4) position=position+up*v;
        if(dir==5) position=position-up*v;
    }
    void processMouse(float xoff,float yoff){
        xoff*=sensitivity;yoff*=sensitivity;
        yaw+=xoff;pitch+=yoff;
        pitch=std::max(-89.0f,std::min(89.0f,pitch));
        updateVectors();
    }
private:
    void updateVectors(){
        Vec3 nf;
        float yr=yaw*3.14159265359f/180.0f;
        float pr=pitch*3.14159265359f/180.0f;
        nf.x=std::cos(yr)*std::cos(pr);
        nf.y=std::sin(pr);
        nf.z=std::sin(yr)*std::cos(pr);
        front=nf.normalize();
        right=front.cross(worldUp).normalize();
        up=right.cross(front).normalize();
    }
};

struct BodyInstance{
    Vec3 orbitAxis;
    float orbitRadius;
    float orbitSpeed;
    float selfSpeed;
    float scale;
    float phase;
    GLuint textureId;
    const Mesh* mesh;
};

class SolarSystemApp{
private:
    sf::Window window;
    Camera camera;
    Shader shader;
    Shader ringShader;
    Mesh meshCentre;
    Mesh meshOrbit;
    GLuint texCentre;
    GLuint texOrbit;
    std::vector<BodyInstance> bodies;
    bool firstMouse;
    sf::Vector2i lastMouse;
    float timeValue;

    GLuint ringVao;
    GLuint ringVbo;
    int ringVertexCount;

public:
    SolarSystemApp():firstMouse(true),timeValue(0.0f),ringVao(0),ringVbo(0),ringVertexCount(0){
        sf::ContextSettings settings;
        settings.depthBits=24;
        settings.stencilBits=8;
        settings.antialiasingLevel=4;
        settings.majorVersion=3;
        settings.minorVersion=3;
        window.create(sf::VideoMode(1920,1080),"Solar System",sf::Style::Default,settings);
        window.setVerticalSyncEnabled(true);
        window.setMouseCursorVisible(false);
        window.setMouseCursorGrabbed(true);

        glewExperimental=GL_TRUE;
        if(glewInit()!=GLEW_OK) throw std::runtime_error("GLEW init failed");

        glEnable(GL_DEPTH_TEST);
        glEnable(GL_CULL_FACE);
        glCullFace(GL_BACK);
        glFrontFace(GL_CCW);

        initResources();
        initBodies();
    }

    ~SolarSystemApp(){
        if(ringVao) glDeleteVertexArrays(1,&ringVao);
        if(ringVbo) glDeleteBuffers(1,&ringVbo);
        if(texCentre) glDeleteTextures(1,&texCentre);
        if(texOrbit) glDeleteTextures(1,&texOrbit);
    }

    void run(){
        sf::Clock clock;
        while(window.isOpen()){
            float dt=clock.restart().asSeconds();
            handleInput(dt);
            update(dt);
            render();
        }
    }

private:
    void initRing(){
        const int segments=256;
        ringVertexCount=segments;
        std::vector<float> pts;
        pts.reserve(segments*3);
        for(int i=0;i<segments;i++){
            float a=(float)i/(float)segments*2.0f*3.14159265359f;
            pts.push_back(std::cos(a));
            pts.push_back(0.0f);
            pts.push_back(std::sin(a));
        }

        glGenVertexArrays(1,&ringVao);
        glGenBuffers(1,&ringVbo);

        glBindVertexArray(ringVao);
        glBindBuffer(GL_ARRAY_BUFFER,ringVbo);
        glBufferData(GL_ARRAY_BUFFER,(GLsizeiptr)(pts.size()*sizeof(float)),pts.data(),GL_STATIC_DRAW);
        glVertexAttribPointer(0,3,GL_FLOAT,GL_FALSE,3*sizeof(float),(void*)0);
        glEnableVertexAttribArray(0);
        glBindVertexArray(0);
    }

    void initResources(){
        if(!meshCentre.loadFromObj("objectCentre.obj")) throw std::runtime_error("objectCentre.obj missing or invalid");
        if(!meshOrbit.loadFromObj("objectOrbit.obj")) throw std::runtime_error("objectOrbit.obj missing or invalid");

        std::string centreTexFile=pickTextureFile("objectCentre");
        std::string orbitTexFile=pickTextureFile("objectOrbit");
        if(centreTexFile.empty()) std::cerr<<"Texture file not found for objectCentre (expected objectCentre.png/jpg/...)"<<std::endl;
        if(orbitTexFile.empty()) std::cerr<<"Texture file not found for objectOrbit (expected objectOrbit.png/jpg/...)"<<std::endl;

        texCentre=centreTexFile.empty()?0:loadTexture2D(centreTexFile);
        texOrbit=orbitTexFile.empty()?0:loadTexture2D(orbitTexFile);

        std::string vs=R"(
#version 330 core
layout(location=0) in vec3 aPos;
layout(location=1) in vec3 aNormal;
layout(location=2) in vec2 aTex;

out vec3 FragPos;
out vec3 Normal;
out vec2 TexCoord;

uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;

void main(){
    FragPos = vec3(model * vec4(aPos,1.0));
    Normal = mat3(transpose(inverse(model))) * aNormal;
    TexCoord = aTex;
    gl_Position = projection * view * vec4(FragPos,1.0);
}
)";
        std::string fs=R"(
#version 330 core
out vec4 FragColor;

in vec3 FragPos;
in vec3 Normal;
in vec2 TexCoord;

uniform sampler2D diffuseTexture;
uniform vec3 viewPos;

void main(){
    vec3 albedo = texture(diffuseTexture, TexCoord).rgb;
    vec3 N = normalize(Normal);
    vec3 V = normalize(viewPos - FragPos);
    vec3 L = normalize(vec3(1.0,1.0,0.5));
    float diff = max(dot(N,L), 0.0);
    vec3 R = reflect(-L, N);
    float spec = pow(max(dot(V,R),0.0), 32.0);
    vec3 color = albedo * (0.15 + 0.85*diff) + vec3(0.25)*spec;
    FragColor = vec4(color,1.0);
}
)";
        if(!shader.compile(vs,fs)) throw std::runtime_error("Shader compile failed");
        shader.use();
        shader.setInt("diffuseTexture",0);

        std::string rvs=R"(
#version 330 core
layout(location=0) in vec3 aPos;
uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;
void main(){
    gl_Position = projection * view * model * vec4(aPos, 1.0);
}
)";
        std::string rfs=R"(
#version 330 core
out vec4 FragColor;
uniform vec3 color;
void main(){
    FragColor = vec4(color, 1.0);
}
)";
        if(!ringShader.compile(rvs,rfs)) throw std::runtime_error("Ring shader compile failed");
        initRing();
    }

    void initBodies(){
        bodies.clear();

        BodyInstance sun;
        sun.mesh=&meshCentre;
        sun.textureId=texCentre?texCentre:texOrbit;
        sun.orbitAxis=Vec3(0,1,0);
        sun.orbitRadius=0.0f;
        sun.orbitSpeed=0.0f;
        sun.selfSpeed=0.6f;
        sun.scale=0.28f;
        sun.phase=0.0f;
        bodies.push_back(sun);

        int orbitCount=6;
        for(int i=0;i<orbitCount;i++){
            BodyInstance p;
            p.mesh=&meshOrbit;
            p.textureId=texOrbit?texOrbit:texCentre;
            p.orbitAxis=Vec3(0,1,0);
            p.orbitRadius=10.0f + i*5.0f;
            p.orbitSpeed=0.5f + 0.18f*i;
            p.selfSpeed=0.8f + 0.25f*i;
            p.scale=(1.3f - 0.12f*i) * 0.5f;
            p.phase=0.7f*i;
            bodies.push_back(p);
        }
    }

    void handleInput(float dt){
        sf::Event e;
        while(window.pollEvent(e)){
            if(e.type==sf::Event::Closed) window.close();
            else if(e.type==sf::Event::Resized) glViewport(0,0,e.size.width,e.size.height);
            else if(e.type==sf::Event::MouseMoved){
                if(firstMouse){
                    lastMouse=sf::Vector2i(e.mouseMove.x,e.mouseMove.y);
                    firstMouse=false;
                }
                float xoff=(float)e.mouseMove.x-(float)lastMouse.x;
                float yoff=(float)lastMouse.y-(float)e.mouseMove.y;
                lastMouse=sf::Vector2i(e.mouseMove.x,e.mouseMove.y);
                camera.processMouse(xoff,yoff);
            }else if(e.type==sf::Event::KeyPressed){
                if(e.key.code==sf::Keyboard::Escape) window.close();
            }
        }

        if(sf::Keyboard::isKeyPressed(sf::Keyboard::W)) camera.processKeyboard(0,dt);
        if(sf::Keyboard::isKeyPressed(sf::Keyboard::S)) camera.processKeyboard(1,dt);
        if(sf::Keyboard::isKeyPressed(sf::Keyboard::A)) camera.processKeyboard(2,dt);
        if(sf::Keyboard::isKeyPressed(sf::Keyboard::D)) camera.processKeyboard(3,dt);
        if(sf::Keyboard::isKeyPressed(sf::Keyboard::Space)) camera.processKeyboard(4,dt);
        if(sf::Keyboard::isKeyPressed(sf::Keyboard::LControl)) camera.processKeyboard(5,dt);
    }

    void update(float dt){
        timeValue += dt;
    }

    Mat4 modelForBody(const BodyInstance& b, float t) const{
        float orbitAngle = b.orbitSpeed * t + b.phase;
        float selfAngle  = b.selfSpeed  * t;

        Vec3 pos(0,0,0);
        if(b.orbitRadius > 0.0f){
            pos.x = std::cos(orbitAngle) * b.orbitRadius;
            pos.z = std::sin(orbitAngle) * b.orbitRadius;
        }

    		if (b.orbitRadius == 0.0f) {
        		pos.y -= 5.0f;
    		}

        Mat4 m = Mat4::translate(pos);
      
        if (b.orbitRadius == 0.0f) {
        	m = m * Mat4::rotate(3.14159265359f/2, Vec3(-1, 0, 0));
    	  }
      
    	  m = m * Mat4::rotate(selfAngle, Vec3(0, 0, 1));
        m = m * Mat4::scale(b.scale,b.scale,b.scale);
        return m;
    }

    void renderRings(const Mat4& view, const Mat4& proj){
        ringShader.use();
        ringShader.setMat4("view", view);
        ringShader.setMat4("projection", proj);
        ringShader.setVec3("color", Vec3(0.6f, 0.6f, 0.9f));

        glBindVertexArray(ringVao);
        glDisable(GL_CULL_FACE);
        glLineWidth(2.0f);

        for(size_t i=1;i<bodies.size();i++){
            float r = bodies[i].orbitRadius;
            Mat4 model = Mat4::translate(0.0f, 0.01f, 0.0f) * Mat4::scale(r, 1.0f, r);
            ringShader.setMat4("model", model);
            glDrawArrays(GL_LINE_LOOP, 0, ringVertexCount);
        }

        glLineWidth(1.0f);
        glEnable(GL_CULL_FACE);
        glBindVertexArray(0);
    }

    void render(){
        glClearColor(0.04f,0.04f,0.08f,1.0f);
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);

        Mat4 view = camera.view();
        Mat4 proj = Mat4::perspective(camera.fov, (float)window.getSize().x/(float)window.getSize().y, 0.1f, 400.0f);

        renderRings(view, proj);

        shader.use();
        shader.setMat4("view", view);
        shader.setMat4("projection", proj);
        shader.setVec3("viewPos", camera.position);

        for(const auto& b: bodies){
            Mat4 model = modelForBody(b, timeValue);
            shader.setMat4("model", model);
            glActiveTexture(GL_TEXTURE0);
            glBindTexture(GL_TEXTURE_2D, b.textureId);
            b.mesh->draw();
        }

        glBindTexture(GL_TEXTURE_2D,0);
        window.display();
    }
};

int main(){
    try{
        SolarSystemApp app;
        app.run();
    }catch(const std::exception& e){
        std::cerr<<e.what()<<std::endl;
        return 1;
    }
    return 0;
}
