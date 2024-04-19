#version 430 


struct nucleon
{
    vec4 pos;
    vec4 v;
    float type;
    float r;
    float m;
    float pad1;
    vec4 rot;
    vec4 rotv;
    float animate;
    float q;
    vec4 color;
};



layout(std430, binding=0) buffer nucleons_in
{
    nucleon nucleons[];
} In;

//layout(std430, binding=0) buffer nucleons_in


layout (location = 0) in vec3 position;
layout (location = 1) in vec3 normal;

uniform vec3 objectColor;
uniform int mode;
uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;

out nucleonData {
    nucleon out_a;
};

//out vec4 nucleon_position;
out vec3 Normal;
out vec3 ObjectColor;
out vec3 FragPos;  

//out nucleon currentnucleon;



void main()
{
    if (mode==0){  //vbo merge nucleons 
//        float factor = 0.001;
        gl_Position = projection * view * model * vec4(position, 1.0f);
        ObjectColor = objectColor;
        FragPos = vec3(model * vec4(position, 1.0f));
        Normal = normal;
    }
    if (mode==1){ //ssbo nucleons
        bool bug = false; 
        float factor = 0.001;
        nucleon currentnucleon = In.nucleons[gl_InstanceID];
        vec4 vposition = vec4(position * currentnucleon.r * factor +  currentnucleon.pos.xyz*factor, 1.0f) ;
        //nucleon_position = currentnucleon.pos*factor;
        gl_Position = projection * view * vposition;
//        if (currentnucleon.pos.x != 515.0){
//            bug = true;
//        }
        ObjectColor = currentnucleon.color.xyz;
        if (bug){
            ObjectColor = vec3(1,0,0);
        }
        if (currentnucleon.animate>0) ObjectColor = vec3(0,1,0);
        FragPos = vposition.xyz;
        Normal = normal;
    }
}