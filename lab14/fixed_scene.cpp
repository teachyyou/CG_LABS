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

struct LightSource{
    int type;Vec3 position;Vec3 direction;Vec3 color;float intensity;float cutoff;float outerCutoff;bool enabled;
    LightSource():type(0),position(0,2,0),direction(0,-1,0),color(1,1,1),intensity(1.0f),
        cutoff(std::cos(15.0f*3.14159265359f/180.0f)),outerCutoff(std::cos(25.0f*3.14159265359f/180.0f)),enabled(true){}
};

class Camera{
public:
    Vec3 position,front,up,right,worldUp;float yaw,pitch,speed,sensitivity,fov;
    Camera(const Vec3&pos=Vec3(0.0f,3.0f,10.0f)):position(pos),worldUp(0.0f,1.0f,0.0f),yaw(-90.0f),pitch(-20.0f),speed(5.0f),sensitivity(0.1f),fov(45.0f){updateCameraVectors();}
    Mat4 getViewMatrix(){return Mat4::lookAt(position,position+front,up);}
    void processKeyboard(int direction,float deltaTime){
        float v=speed*deltaTime;
        if(direction==0)position=position+front*v;
        if(direction==1)position=position-front*v;
        if(direction==2)position=position-right*v;
        if(direction==3)position=position+right*v;
        if(direction==4)position=position+up*v;
        if(direction==5)position=position-up*v;
    }
    void processMouseMovement(float xoffset,float yoffset){
        xoffset*=sensitivity;yoffset*=sensitivity;
        yaw+=xoffset;pitch+=yoffset;
        pitch=std::max(-89.0f,std::min(89.0f,pitch));
        updateCameraVectors();
    }
private:
    void updateCameraVectors(){
        Vec3 nf;float yr=yaw*3.14159265359f/180.0f;float pr=pitch*3.14159265359f/180.0f;
        nf.x=std::cos(yr)*std::cos(pr);nf.y=std::sin(pr);nf.z=std::sin(yr)*std::cos(pr);
        front=nf.normalize();right=front.cross(worldUp).normalize();up=right.cross(front).normalize();
    }
};

class SceneObject{
private:
    GLuint vao,vbo,ebo;
    std::vector<Vertex> vertices;
    std::vector<unsigned int> indices;
    GLuint textureId;
    bool hasTexture;
    bool isReady;
public:
    Mat4 modelMatrix;
    int lightingModel;
    Vec3 baseColor;
    float roughness;
    float metallic;
    std::string name;

    SceneObject():vao(0),vbo(0),ebo(0),textureId(0),hasTexture(false),isReady(false),modelMatrix(Mat4::identity()),lightingModel(0),baseColor(0.8f,0.8f,0.8f),roughness(0.5f),metallic(0.0f){}
    ~SceneObject(){if(vao)glDeleteVertexArrays(1,&vao);if(vbo)glDeleteBuffers(1,&vbo);if(ebo)glDeleteBuffers(1,&ebo);if(textureId)glDeleteTextures(1,&textureId);}

    static GLuint loadTextureFromFile(const std::string&filename){
        int width=0,height=0,channels=0;
        stbi_set_flip_vertically_on_load(true);
        unsigned char* data=stbi_load(filename.c_str(),&width,&height,&channels,0);
        if(!data){std::cerr<<"Failed to load texture: "<<filename<<std::endl;return 0;}

        GLenum format=GL_RGB;
        if(channels==1)format=GL_RED;
        else if(channels==3)format=GL_RGB;
        else if(channels==4)format=GL_RGBA;

        GLuint tex=0;
        glGenTextures(1,&tex);
        glBindTexture(GL_TEXTURE_2D,tex);
        glPixelStorei(GL_UNPACK_ALIGNMENT,1);
        glTexImage2D(GL_TEXTURE_2D,0,format,width,height,0,format,GL_UNSIGNED_BYTE,data);
        glGenerateMipmap(GL_TEXTURE_2D);
        glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_WRAP_S,GL_REPEAT);
        glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_WRAP_T,GL_REPEAT);
        glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MIN_FILTER,GL_LINEAR_MIPMAP_LINEAR);
        glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MAG_FILTER,GL_LINEAR);
        glBindTexture(GL_TEXTURE_2D,0);
        stbi_image_free(data);
        return tex;
    }

    void loadTexture(const std::string&textureFile){
        if(textureFile.empty()){
            hasTexture=false;
            if(textureId){glDeleteTextures(1,&textureId);textureId=0;}
            return;
        }
        if(textureId)glDeleteTextures(1,&textureId);
        textureId=loadTextureFromFile(textureFile);
        hasTexture=textureId!=0;
    }

    bool loadFromOBJ(const std::string&filename,const Vec3&color,const std::string&textureFile=""){
        std::ifstream file(filename);
        if(!file.is_open()){std::cerr<<"Не удалось открыть OBJ: "<<filename<<std::endl;return false;}

        std::vector<Vec3> tempPositions;
        std::vector<Vec3> tempNormals;
        std::vector<Vec2> tempTexcoords;
        vertices.clear();indices.clear();

        std::string line;
        while(std::getline(file,line)){
            if(line.empty())continue;
            std::istringstream iss(line);
            std::string prefix;iss>>prefix;

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
                    std::string token;std::vector<std::string> parts;
                    while(std::getline(viss,token,'/'))parts.push_back(token);

                    Vertex vert;
                    if(!parts.empty()&&!parts[0].empty()){
                        int idx=std::stoi(parts[0]);
                        if(idx<0)idx=(int)tempPositions.size()+idx+1;
                        idx-=1;
                        if(idx>=0&&idx<(int)tempPositions.size())vert.position=tempPositions[idx];
                    }
                    if(parts.size()>1&&!parts[1].empty()){
                        int idx=std::stoi(parts[1]);
                        if(idx<0)idx=(int)tempTexcoords.size()+idx+1;
                        idx-=1;
                        if(idx>=0&&idx<(int)tempTexcoords.size())vert.texcoord=tempTexcoords[idx];
                    }else{
                        vert.texcoord=Vec2(0.0f,0.0f);
                    }
                    if(parts.size()>2&&!parts[2].empty()){
                        int idx=std::stoi(parts[2]);
                        if(idx<0)idx=(int)tempNormals.size()+idx+1;
                        idx-=1;
                        if(idx>=0&&idx<(int)tempNormals.size())vert.normal=tempNormals[idx];
                    }else{
                        vert.normal=Vec3(0.0f,1.0f,0.0f);
                    }
                    vertices.push_back(vert);
                    indices.push_back((unsigned int)vertices.size()-1);
                }
            }
        }

        if(vertices.empty()||indices.empty()){std::cerr<<"OBJ пустой или без граней: "<<filename<<std::endl;return false;}
        if(tempNormals.empty())computeNormals();
        if(tempTexcoords.empty())generatePlanarUVs();

        baseColor=color;
        loadTexture(textureFile);
        setupBuffers();
        isReady=true;
        return true;
    }

    void createFloor(const Vec3&color){
        vertices.clear();indices.clear();baseColor=color;
        textureId=loadTextureFromFile("floor_texture.jpg");
        hasTexture=textureId!=0;
        float size=15.0f,y=0.0f;
        vertices.push_back(Vertex(Vec3(-size,y,-size),Vec3(0.0f,1.0f,0.0f),Vec2(0.0f,0.0f)));
        vertices.push_back(Vertex(Vec3( size,y,-size),Vec3(0.0f,1.0f,0.0f),Vec2(10.0f,0.0f)));
        vertices.push_back(Vertex(Vec3( size,y, size),Vec3(0.0f,1.0f,0.0f),Vec2(10.0f,10.0f)));
        vertices.push_back(Vertex(Vec3(-size,y, size),Vec3(0.0f,1.0f,0.0f),Vec2(0.0f,10.0f)));
        indices.insert(indices.end(),{0,1,2,0,2,3});
        setupBuffers();isReady=true;name="Floor";
    }

    void render(GLuint shaderProgram){
        if(!isReady)return;
        glUseProgram(shaderProgram);

        GLint modelLoc=glGetUniformLocation(shaderProgram,"model");
        if(modelLoc!=-1)glUniformMatrix4fv(modelLoc,1,GL_FALSE,modelMatrix.m);

        GLint colorLoc=glGetUniformLocation(shaderProgram,"material.baseColor");
        GLint roughLoc=glGetUniformLocation(shaderProgram,"material.roughness");
        GLint metalLoc=glGetUniformLocation(shaderProgram,"material.metallic");
        GLint lightingModelLoc=glGetUniformLocation(shaderProgram,"material.lightingModel");
        GLint hasTextureLoc=glGetUniformLocation(shaderProgram,"material.hasTexture");

        if(colorLoc!=-1)glUniform3f(colorLoc,baseColor.x,baseColor.y,baseColor.z);
        if(roughLoc!=-1)glUniform1f(roughLoc,roughness);
        if(metalLoc!=-1)glUniform1f(metalLoc,metallic);
        if(lightingModelLoc!=-1)glUniform1i(lightingModelLoc,lightingModel);
        if(hasTextureLoc!=-1)glUniform1i(hasTextureLoc,hasTexture?1:0);

        if(hasTexture){
            glActiveTexture(GL_TEXTURE0);
            glBindTexture(GL_TEXTURE_2D,textureId);
            GLint texLoc=glGetUniformLocation(shaderProgram,"material.diffuseTexture");
            if(texLoc!=-1)glUniform1i(texLoc,0);
        }

        glBindVertexArray(vao);
        glDrawElements(GL_TRIANGLES,(GLsizei)indices.size(),GL_UNSIGNED_INT,nullptr);
        glBindVertexArray(0);
        glBindTexture(GL_TEXTURE_2D,0);
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
        for(auto& v:vertices)v.normal=Vec3(0.0f,0.0f,0.0f);
        for(size_t i=0;i+2<indices.size();i+=3){
            Vertex& v0=vertices[indices[i]];
            Vertex& v1=vertices[indices[i+1]];
            Vertex& v2=vertices[indices[i+2]];
            Vec3 e1=v1.position-v0.position;
            Vec3 e2=v2.position-v0.position;
            Vec3 n=e1.cross(e2).normalize();
            v0.normal=v0.normal+n;v1.normal=v1.normal+n;v2.normal=v2.normal+n;
        }
        for(auto& v:vertices)v.normal=v.normal.normalize();
    }

    void generatePlanarUVs(){
        Vec3 minP(1e9f,1e9f,1e9f),maxP(-1e9f,-1e9f,-1e9f);
        for(const auto& v:vertices){
            minP.x=std::min(minP.x,v.position.x);minP.y=std::min(minP.y,v.position.y);minP.z=std::min(minP.z,v.position.z);
            maxP.x=std::max(maxP.x,v.position.x);maxP.y=std::max(maxP.y,v.position.y);maxP.z=std::max(maxP.z,v.position.z);
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

class ShaderManager{
private:
    GLuint programId;
public:
    ShaderManager():programId(0){}
    ~ShaderManager(){if(programId)glDeleteProgram(programId);}
    bool compileShader(const std::string&vertexShader,const std::string&fragmentShader){
        const char* vCode=vertexShader.c_str();
        const char* fCode=fragmentShader.c_str();
        GLuint v=glCreateShader(GL_VERTEX_SHADER);
        glShaderSource(v,1,&vCode,nullptr);
        glCompileShader(v);
        if(!checkCompile(v,false))return false;
        GLuint f=glCreateShader(GL_FRAGMENT_SHADER);
        glShaderSource(f,1,&fCode,nullptr);
        glCompileShader(f);
        if(!checkCompile(f,false))return false;
        programId=glCreateProgram();
        glAttachShader(programId,v);
        glAttachShader(programId,f);
        glLinkProgram(programId);
        glDeleteShader(v);
        glDeleteShader(f);
        return checkCompile(programId,true);
    }
    GLuint getProgramID()const{return programId;}
    void use()const{glUseProgram(programId);}
    void setMat4(const std::string&name,const Mat4&mat)const{GLint loc=glGetUniformLocation(programId,name.c_str());if(loc!=-1)glUniformMatrix4fv(loc,1,GL_FALSE,mat.m);}
    void setVec3(const std::string&name,const Vec3&vec)const{GLint loc=glGetUniformLocation(programId,name.c_str());if(loc!=-1)glUniform3f(loc,vec.x,vec.y,vec.z);}
    void setInt(const std::string&name,int value)const{GLint loc=glGetUniformLocation(programId,name.c_str());if(loc!=-1)glUniform1i(loc,value);}
    void setFloat(const std::string&name,float value)const{GLint loc=glGetUniformLocation(programId,name.c_str());if(loc!=-1)glUniform1f(loc,value);}
private:
    bool checkCompile(GLuint obj,bool isProgram){
        GLint success=0;char info[1024];
        if(!isProgram){
            glGetShaderiv(obj,GL_COMPILE_STATUS,&success);
            if(!success){glGetShaderInfoLog(obj,1024,nullptr,info);std::cerr<<info<<std::endl;return false;}
        }else{
            glGetProgramiv(obj,GL_LINK_STATUS,&success);
            if(!success){glGetProgramInfoLog(obj,1024,nullptr,info);std::cerr<<info<<std::endl;return false;}
        }
        return true;
    }
};

class OpenGLScene{
private:
    sf::Window window;
    Camera camera;
    std::vector<std::unique_ptr<SceneObject>> objects;
    std::vector<LightSource> lights;
    ShaderManager shader;
    int currentLightingModel;
    int selectedLight;
    float timeValue;
    bool firstMouse;
    sf::Vector2i lastMousePos;
    float lightMoveSpeed;
    bool movingLight;

public:
    OpenGLScene():currentLightingModel(-1),selectedLight(0),timeValue(0.0f),firstMouse(true),lightMoveSpeed(5.0f),movingLight(false){
        sf::ContextSettings settings;
        settings.depthBits=24;settings.stencilBits=8;settings.antialiasingLevel=4;settings.majorVersion=3;settings.minorVersion=3;
        window.create(sf::VideoMode(1200,800),"3D Scene with Lighting",sf::Style::Default,settings);
        window.setVerticalSyncEnabled(true);
        window.setMouseCursorVisible(false);
        window.setMouseCursorGrabbed(true);

        glewExperimental=GL_TRUE;
        if(glewInit()!=GLEW_OK)throw std::runtime_error("GLEW init failed");

        glEnable(GL_DEPTH_TEST);
        glEnable(GL_CULL_FACE);
        glCullFace(GL_BACK);
        glFrontFace(GL_CCW);

        initScene();
        initLights();
        compileShader();
    }

    void run(){while(window.isOpen()){handleInput();update(0.016f);render();}}

    void printControls(){
        std::cout<<"\nWASD Space/Ctrl mouse\n";
        std::cout<<"0: per-object lighting, 1/2/3: global Phong/Toon/Cook-Torrance\n";
        std::cout<<"F1/F2/F3 toggle lights, arrows select light and intensity\n";
        std::cout<<"IJKL U/O move selected (point/spot), +/- spot cone\n";
        std::cout<<"P change per-object model\n";
    }

private:
    void initScene(){
        auto floor=std::make_unique<SceneObject>();
        floor->createFloor(Vec3(0.6f,0.6f,0.6f));
        floor->lightingModel=0;
        floor->modelMatrix=Mat4::translate(0.0f,0.0f,0.0f);
        floor->roughness=0.8f;
        objects.push_back(std::move(floor));

        auto obj1=std::make_unique<SceneObject>();obj1->name="Obj1";
        if(obj1->loadFromOBJ("model1.obj",Vec3(1.0f,1.0f,1.0f),"texture1.jpg")){
            obj1->lightingModel=2;obj1->modelMatrix=Mat4::translate(-4.0f,1.0f,0.0f)*Mat4::scale(1.0f,1.0f,1.0f);
            obj1->metallic=0.8f;obj1->roughness=0.3f;objects.push_back(std::move(obj1));
        }

        auto obj2=std::make_unique<SceneObject>();obj2->name="Obj2";
        if(obj2->loadFromOBJ("model2.obj",Vec3(1.0f,1.0f,1.0f),"texture2.jpg")){
            obj2->lightingModel=2;obj2->modelMatrix=Mat4::translate(-2.0f,1.0f,0.0f)*Mat4::scale(1.0f,1.0f,1.0f);
            obj2->metallic=0.9f;obj2->roughness=0.2f;objects.push_back(std::move(obj2));
        }

        auto obj3=std::make_unique<SceneObject>();obj3->name="Obj3";
        if(obj3->loadFromOBJ("model3.obj",Vec3(1.0f,1.0f,1.0f),"texture3.jpg")){
            obj3->lightingModel=2;obj3->modelMatrix=Mat4::translate(0.0f,1.0f,0.0f)*Mat4::scale(1.0f,1.0f,1.0f);
            obj3->metallic=0.7f;obj3->roughness=0.4f;objects.push_back(std::move(obj3));
        }

        auto obj4=std::make_unique<SceneObject>();obj4->name="Obj4";
        if(obj4->loadFromOBJ("model4.obj",Vec3(1.0f,1.0f,1.0f),"texture4.jpg")){
            obj4->lightingModel=2;obj4->modelMatrix=Mat4::translate(2.0f,1.0f,0.0f)*Mat4::scale(1.0f,1.0f,1.0f);
            obj4->metallic=0.6f;obj4->roughness=0.5f;objects.push_back(std::move(obj4));
        }

        auto obj5=std::make_unique<SceneObject>();obj5->name="Obj5";
        if(obj5->loadFromOBJ("model5.obj",Vec3(1.0f,1.0f,1.0f),"texture5.jpg")){
            obj5->lightingModel=2;obj5->modelMatrix=Mat4::translate(4.0f,1.0f,0.0f)*Mat4::scale(1.0f,1.0f,1.0f);
            obj5->metallic=0.85f;obj5->roughness=0.3f;objects.push_back(std::move(obj5));
        }
    }

    void initLights(){
        LightSource pointLight;pointLight.type=0;pointLight.position=Vec3(-2.0f,3.0f,2.0f);pointLight.color=Vec3(1.0f,0.8f,0.8f);pointLight.intensity=1.5f;lights.push_back(pointLight);
        LightSource directionalLight;directionalLight.type=1;directionalLight.direction=Vec3(-0.5f,-1.0f,-0.5f);directionalLight.color=Vec3(1.0f,1.0f,1.0f);directionalLight.intensity=0.8f;lights.push_back(directionalLight);
        LightSource spotLight;spotLight.type=2;spotLight.position=Vec3(2.0f,3.0f,2.0f);spotLight.direction=Vec3(0.0f,-0.5f,-1.0f);spotLight.color=Vec3(0.8f,0.8f,1.0f);spotLight.intensity=2.0f;spotLight.cutoff=std::cos(15.0f*3.14159265359f/180.0f);spotLight.outerCutoff=std::cos(25.0f*3.14159265359f/180.0f);lights.push_back(spotLight);
    }

    void compileShader(){
        std::string vertexShader=R"(
#version 330 core
layout(location = 0) in vec3 aPos;
layout(location = 1) in vec3 aNormal;
layout(location = 2) in vec2 aTexCoord;

out vec3 FragPos;
out vec3 Normal;
out vec2 TexCoord;

uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;

void main() {
    FragPos = vec3(model * vec4(aPos, 1.0));
    Normal = mat3(transpose(inverse(model))) * aNormal;
    TexCoord = aTexCoord;
    gl_Position = projection * view * vec4(FragPos, 1.0);
}
)";

        std::string fragmentShader=R"(
#version 330 core
out vec4 FragColor;

in vec3 FragPos;
in vec3 Normal;
in vec2 TexCoord;

struct Material {
    vec3 baseColor;
    float roughness;
    float metallic;
    sampler2D diffuseTexture;
    int lightingModel;
    int hasTexture;
};

struct Light {
    int type;
    vec3 position;
    vec3 direction;
    vec3 color;
    float intensity;
    float cutoff;
    float outerCutoff;
    int enabled;
};

uniform Material material;
uniform Light lights[8];
uniform int lightCount;
uniform vec3 viewPos;
uniform int activeLightingModel;

const float PI = 3.14159265359;

vec3 calculatePhongPointLight(Light light, vec3 normal, vec3 viewDir, vec3 diffuseColor) {
    if (light.enabled == 0) return vec3(0.0);
    vec3 lightDir = normalize(light.position - FragPos);
    float distance = length(light.position - FragPos);
    float attenuation = 1.0 / (1.0 + 0.1 * distance + 0.01 * distance * distance);
    float diff = max(dot(normal, lightDir), 0.0);
    vec3 diffuse = diff * diffuseColor * light.color;
    vec3 reflectDir = reflect(-lightDir, normal);
    float spec = pow(max(dot(viewDir, reflectDir), 0.0), 32.0);
    vec3 specular = spec * light.color * material.metallic;
    return (diffuse + specular) * light.intensity * attenuation;
}

vec3 calculatePhongDirectionalLight(Light light, vec3 normal, vec3 viewDir, vec3 diffuseColor) {
    if (light.enabled == 0) return vec3(0.0);
    vec3 lightDir = normalize(-light.direction);
    float diff = max(dot(normal, lightDir), 0.0);
    vec3 diffuse = diff * diffuseColor * light.color;
    vec3 reflectDir = reflect(-lightDir, normal);
    float spec = pow(max(dot(viewDir, reflectDir), 0.0), 32.0);
    vec3 specular = spec * light.color * material.metallic;
    return (diffuse + specular) * light.intensity;
}

vec3 calculatePhongSpotLight(Light light, vec3 normal, vec3 viewDir, vec3 diffuseColor) {
    if (light.enabled == 0) return vec3(0.0);
    vec3 lightDir = normalize(light.position - FragPos);
    float distance = length(light.position - FragPos);
    float attenuation = 1.0 / (1.0 + 0.1 * distance + 0.01 * distance * distance);
    float theta = dot(lightDir, normalize(-light.direction));
    float epsilon = light.cutoff - light.outerCutoff;
    float intensity = clamp((theta - light.outerCutoff) / epsilon, 0.0, 1.0);
    if (theta <= light.outerCutoff) return vec3(0.0);
    float diff = max(dot(normal, lightDir), 0.0);
    vec3 diffuse = diff * diffuseColor * light.color;
    vec3 reflectDir = reflect(-lightDir, normal);
    float spec = pow(max(dot(viewDir, reflectDir), 0.0), 32.0);
    vec3 specular = spec * light.color * material.metallic;
    return (diffuse + specular) * light.intensity * attenuation * intensity;
}

vec3 calculateToonLight(Light light, vec3 normal, vec3 diffuseColor, vec3 viewDir) {
    if (light.enabled == 0) return vec3(0.0);
    vec3 lightDir = (light.type == 1) ? normalize(-light.direction) : normalize(light.position - FragPos);
    float diff = dot(normal, lightDir);
    if (diff > 0.95) diff = 1.0;
    else if (diff > 0.85) diff = 0.9;
    else if (diff > 0.75) diff = 0.8;
    else if (diff > 0.65) diff = 0.7;
    else if (diff > 0.55) diff = 0.6;
    else if (diff > 0.45) diff = 0.5;
    else if (diff > 0.35) diff = 0.4;
    else if (diff > 0.25) diff = 0.3;
    else if (diff > 0.15) diff = 0.2;
    else if (diff > 0.05) diff = 0.1;
    else diff = 0.05;
    float edge = dot(normal, viewDir);
    if (edge < 0.2) diff = 0.0;
    return diff * diffuseColor * light.color * light.intensity;
}

float DistributionGGX(vec3 N, vec3 H, float roughness) {
    float a = roughness * roughness;
    float a2 = a * a;
    float NdotH = max(dot(N, H), 0.0);
    float NdotH2 = NdotH * NdotH;
    float denom = (NdotH2 * (a2 - 1.0) + 1.0);
    denom = PI * denom * denom;
    return a2 / max(denom, 0.0000001);
}

float GeometrySchlickGGX(float NdotV, float roughness) {
    float r = (roughness + 1.0);
    float k = (r * r) / 8.0;
    float denom = NdotV * (1.0 - k) + k;
    return NdotV / denom;
}

float GeometrySmith(vec3 N, vec3 V, vec3 L, float roughness) {
    float NdotV = max(dot(N, V), 0.0);
    float NdotL = max(dot(N, L), 0.0);
    float ggx1 = GeometrySchlickGGX(NdotV, roughness);
    float ggx2 = GeometrySchlickGGX(NdotL, roughness);
    return ggx1 * ggx2;
}

vec3 fresnelSchlick(float cosTheta, vec3 F0) {
    return F0 + (1.0 - F0) * pow(1.0 - cosTheta, 5.0);
}

vec3 calculateCookTorranceLight(Light light, vec3 normal, vec3 viewDir, vec3 albedo) {
    if (light.enabled == 0) return vec3(0.0);

    vec3 lightDir;
    float attenuation = 1.0;

    if (light.type == 1) {
        lightDir = normalize(-light.direction);
    } else {
        lightDir = normalize(light.position - FragPos);
        float distance = length(light.position - FragPos);
        attenuation = 1.0 / (1.0 + 0.1 * distance + 0.01 * distance * distance);
    }

    vec3 halfwayDir = normalize(viewDir + lightDir);

    vec3 F0 = vec3(0.04);
    F0 = mix(F0, albedo, material.metallic);

    float NDF = DistributionGGX(normal, halfwayDir, material.roughness);
    float G = GeometrySmith(normal, viewDir, lightDir, material.roughness);
    vec3 F = fresnelSchlick(max(dot(halfwayDir, viewDir), 0.0), F0);

    vec3 numerator = NDF * G * F;
    float denominator = 4.0 * max(dot(normal, viewDir), 0.0) * max(dot(normal, lightDir), 0.0);
    vec3 specular = numerator / max(denominator, 0.001);

    vec3 kS = F;
    vec3 kD = vec3(1.0) - kS;
    kD *= 1.0 - material.metallic;

    float NdotL = max(dot(normal, lightDir), 0.0);

    if (light.type == 2) {
        float theta = dot(lightDir, normalize(-light.direction));
        float epsilon = light.cutoff - light.outerCutoff;
        float spotIntensity = clamp((theta - light.outerCutoff) / epsilon, 0.0, 1.0);
        if (theta < light.outerCutoff) return vec3(0.0);
        attenuation *= spotIntensity;
    }

    return (kD * albedo / PI + specular) * light.color * NdotL * light.intensity * attenuation;
}

void main() {
    vec3 norm = normalize(Normal);
    vec3 viewDir = normalize(viewPos - FragPos);

    vec3 albedo = material.baseColor;
    if (material.hasTexture == 1) {
        albedo = texture(material.diffuseTexture, TexCoord).rgb * material.baseColor;
    }

    vec3 result = vec3(0.05) * albedo;

    int lightingModelToUse = (activeLightingModel >= 0) ? activeLightingModel : material.lightingModel;

    for (int i = 0; i < lightCount; i++) {
        if (lightingModelToUse == 0) {
            if (lights[i].type == 0) result += calculatePhongPointLight(lights[i], norm, viewDir, albedo);
            else if (lights[i].type == 1) result += calculatePhongDirectionalLight(lights[i], norm, viewDir, albedo);
            else result += calculatePhongSpotLight(lights[i], norm, viewDir, albedo);
        } else if (lightingModelToUse == 1) {
            result += calculateToonLight(lights[i], norm, albedo, viewDir);
        } else {
            result += calculateCookTorranceLight(lights[i], norm, viewDir, albedo);
        }
    }

    if (lightingModelToUse == 2) {
        vec3 ambient = vec3(0.03) * albedo;
        result = ambient + result;
        result = result / (result + vec3(1.0));
        result = pow(result, vec3(1.0/2.2));
    }

    FragColor = vec4(result, 1.0);
}
)";

        if(!shader.compileShader(vertexShader,fragmentShader))throw std::runtime_error("Shader compile failed");
    }

    void update(float deltaTime){
        timeValue+=deltaTime;
        if(!movingLight&&!lights.empty())lights[0].position.y=3.0f+std::sin(timeValue*0.5f)*0.5f;
    }

    void render(){
        glClearColor(0.1f,0.1f,0.15f,1.0f);
        glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT);

        Mat4 view=camera.getViewMatrix();
        Mat4 projection=Mat4::perspective(camera.fov,(float)window.getSize().x/(float)window.getSize().y,0.1f,100.0f);

        shader.use();
        shader.setMat4("view",view);
        shader.setMat4("projection",projection);
        shader.setVec3("viewPos",camera.position);
        shader.setInt("activeLightingModel",currentLightingModel);

        shader.setInt("lightCount",(int)lights.size());
        for(size_t i=0;i<lights.size();i++){
            std::string p="lights["+std::to_string(i)+"].";
            shader.setInt(p+"type",lights[i].type);
            shader.setVec3(p+"position",lights[i].position);
            shader.setVec3(p+"direction",lights[i].direction);
            shader.setVec3(p+"color",lights[i].color);
            shader.setFloat(p+"intensity",lights[i].intensity);
            shader.setFloat(p+"cutoff",lights[i].cutoff);
            shader.setFloat(p+"outerCutoff",lights[i].outerCutoff);
            shader.setInt(p+"enabled",lights[i].enabled?1:0);
        }

        for(const auto& obj:objects)obj->render(shader.getProgramID());
        window.display();
    }

    void handleInput(){
        static sf::Clock clock;
        float deltaTime=clock.restart().asSeconds();

        sf::Event event;
        while(window.pollEvent(event)){
            if(event.type==sf::Event::Closed)window.close();
            else if(event.type==sf::Event::Resized)glViewport(0,0,event.size.width,event.size.height);
            else if(event.type==sf::Event::KeyPressed)handleKeyPress(event.key.code,deltaTime);
            else if(event.type==sf::Event::MouseMoved){
                if(firstMouse){lastMousePos=sf::Vector2i(event.mouseMove.x,event.mouseMove.y);firstMouse=false;}
                float xoffset=(float)event.mouseMove.x-(float)lastMousePos.x;
                float yoffset=(float)lastMousePos.y-(float)event.mouseMove.y;
                lastMousePos=sf::Vector2i(event.mouseMove.x,event.mouseMove.y);
                camera.processMouseMovement(xoffset,yoffset);
            }
        }

        if(sf::Keyboard::isKeyPressed(sf::Keyboard::W))camera.processKeyboard(0,deltaTime);
        if(sf::Keyboard::isKeyPressed(sf::Keyboard::S))camera.processKeyboard(1,deltaTime);
        if(sf::Keyboard::isKeyPressed(sf::Keyboard::A))camera.processKeyboard(2,deltaTime);
        if(sf::Keyboard::isKeyPressed(sf::Keyboard::D))camera.processKeyboard(3,deltaTime);
        if(sf::Keyboard::isKeyPressed(sf::Keyboard::Space))camera.processKeyboard(4,deltaTime);
        if(sf::Keyboard::isKeyPressed(sf::Keyboard::LControl))camera.processKeyboard(5,deltaTime);

        if(sf::Keyboard::isKeyPressed(sf::Keyboard::I))moveSelectedLight(2,deltaTime);
        if(sf::Keyboard::isKeyPressed(sf::Keyboard::K))moveSelectedLight(3,deltaTime);
        if(sf::Keyboard::isKeyPressed(sf::Keyboard::L))moveSelectedLight(0,deltaTime);
        if(sf::Keyboard::isKeyPressed(sf::Keyboard::J))moveSelectedLight(1,deltaTime);
        if(sf::Keyboard::isKeyPressed(sf::Keyboard::U))moveSelectedLight(4,deltaTime);
        if(sf::Keyboard::isKeyPressed(sf::Keyboard::O))moveSelectedLight(5,deltaTime);
    }

    void moveSelectedLight(int direction,float deltaTime){
        if(selectedLight==0||selectedLight==2){
            float v=lightMoveSpeed*deltaTime;
            movingLight=true;
            if(direction==0)lights[selectedLight].position.x+=v;
            if(direction==1)lights[selectedLight].position.x-=v;
            if(direction==2)lights[selectedLight].position.y+=v;
            if(direction==3)lights[selectedLight].position.y-=v;
            if(direction==4)lights[selectedLight].position.z+=v;
            if(direction==5)lights[selectedLight].position.z-=v;
        }
    }

    void adjustLightIntensity(bool inc){
        lights[selectedLight].intensity+=inc?0.2f:-0.2f;
        lights[selectedLight].intensity=std::max(0.0f,lights[selectedLight].intensity);
    }

    void adjustSpotlightCone(bool widen){
        if(selectedLight!=2)return;
        float angleChange=2.0f*3.14159265359f/180.0f;
        float currentCutoff=std::acos(lights[2].cutoff);
        float currentOuterCutoff=std::acos(lights[2].outerCutoff);
        if(widen){
            currentCutoff=std::min(currentCutoff+angleChange,60.0f*3.14159265359f/180.0f);
            currentOuterCutoff=std::min(currentOuterCutoff+angleChange*1.2f,70.0f*3.14159265359f/180.0f);
        }else{
            currentCutoff=std::max(currentCutoff-angleChange,5.0f*3.14159265359f/180.0f);
            currentOuterCutoff=std::max(currentOuterCutoff-angleChange*1.2f,currentCutoff+0.05f);
        }
        lights[2].cutoff=std::cos(currentCutoff);
        lights[2].outerCutoff=std::cos(currentOuterCutoff);
    }

    void handleKeyPress(sf::Keyboard::Key key,float){
        if(key==sf::Keyboard::Num0)currentLightingModel=-1;
        else if(key==sf::Keyboard::Num1)currentLightingModel=0;
        else if(key==sf::Keyboard::Num2)currentLightingModel=1;
        else if(key==sf::Keyboard::Num3)currentLightingModel=2;
        else if(key==sf::Keyboard::F1)lights[0].enabled=!lights[0].enabled;
        else if(key==sf::Keyboard::F2)lights[1].enabled=!lights[1].enabled;
        else if(key==sf::Keyboard::F3)lights[2].enabled=!lights[2].enabled;
        else if(key==sf::Keyboard::Up)adjustLightIntensity(true);
        else if(key==sf::Keyboard::Down)adjustLightIntensity(false);
        else if(key==sf::Keyboard::Left){selectedLight=(selectedLight-1+3)%3;movingLight=false;}
        else if(key==sf::Keyboard::Right){selectedLight=(selectedLight+1)%3;movingLight=false;}
        else if(key==sf::Keyboard::Escape)window.close();
        else if(key==sf::Keyboard::P){
            for(auto& obj:objects){
                obj->lightingModel=(obj->lightingModel+1)%3;
                if(obj->lightingModel==2){obj->metallic=0.8f;obj->roughness=0.3f;}
                else{obj->metallic=0.0f;obj->roughness=0.5f;}
            }
        }else if(key==sf::Keyboard::Add||key==sf::Keyboard::Equal)adjustSpotlightCone(true);
        else if(key==sf::Keyboard::Subtract||key==sf::Keyboard::Dash)adjustSpotlightCone(false);
    }
};

int main(){
    try{OpenGLScene scene;scene.printControls();scene.run();}
    catch(const std::exception& e){std::cerr<<e.what()<<std::endl;return -1;}
    return 0;
}
