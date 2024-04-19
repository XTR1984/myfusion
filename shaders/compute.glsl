#version 430
// Set up our compute groups
layout(local_size_x=LOCALSIZEX, local_size_y=1,local_size_z=1) in;

// Input uniforms go here if you need them.
// Some examples:
//uniform vec2 screen_size;
uniform int stage;
uniform vec3 box;
uniform int iTime;
uniform int bondlock;
uniform int gravity;
uniform int atype;
uniform int shake;
uniform int softbox;


//uniform float frame_time;
float BONDR = 4;
uniform float BOND_KOEFF;
uniform float ATTRACT_KOEFF;
uniform float INTERACT_KOEFF;
uniform float ROTA_KOEFF;
float REPULSIOND = -5;
uniform float REPULSION_KOEFF1;
float ATTRACTIOND = 2.0;
uniform float MASS_KOEFF;
uniform float NEARDIST;
uniform float HEAT;
float WIDTH = box.x;
float HEIGHT = box.y;
float DEPTH = box.z;


struct Nucleon
{
    vec4 pos;
    vec4 v;
    float type;
    float r;
    float m;
    float pad;
    vec4 rot;
    vec4 rotv;
    float animate;
    float q;
    vec4 color;
};
// Input buffer
layout(std430, binding=0) buffer nucleons_in
{
    Nucleon nucleons[];
} In;

layout(std430, binding=1) buffer nucleons_out
{
    Nucleon nucleons[];
} Out;

layout(std430, binding=2) buffer near_nucleons
{
    int indexes[][NEARnucleonSMAX];
} Near;


layout(std430, binding=3) buffer far_field
{
    vec4 F;
} Far;


int i = int(gl_GlobalInvocationID);


float rand(vec2 co){
    return fract(sin(dot(co, vec2(12.9898, 78.233))) * 43758.5453);
}


vec4 qmul(vec4 q1, vec4 q2)
{
         return vec4(
             q2.xyz * q1.w + q1.xyz * q2.w + cross(q1.xyz, q2.xyz),
             q1.w * q2.w - dot(q1.xyz, q2.xyz)
         );
}
   
     // Vector rotation with a quaternion
     // http://mathworld.wolfram.com/Quaternion.html
vec3 rotate_vector(vec3 v, vec4 r)
{
         vec4 r_c = r * vec4(-1, -1, -1, 1);
         return qmul(r, qmul(vec4(v, 0), r_c)).xyz;
}

void limits(inout vec3 pos,  inout vec3 v, in float radius){
    v = clamp(v , vec3(-MAXVEL,-MAXVEL,-MAXVEL), vec3(MAXVEL,MAXVEL,MAXVEL));

    if (softbox==1) {
        if (pos.x > WIDTH-radius){
            v.x -= 0.005 ;
        }

        if (pos.y > HEIGHT-radius){
            v.y -= 0.005;
        }

        if (pos.z > DEPTH-radius){
            v.z -= 0.005;
        }

        if (pos.x < radius){
            v.x += 0.005;
        }

        if (pos.y < radius){
            v.y += 0.005;
        }

        if (pos.z < radius){
            v.z += 0.005;
        }
    }
    else {
            if (pos.x > WIDTH-radius){
                pos.x = WIDTH-radius;
                v.x = -v.x ;
            }   

            if (pos.y > HEIGHT-radius){
                pos.y = HEIGHT-radius;
                v.y = - v.y ;
            }

            if (pos.z > DEPTH-radius){
                pos.z = DEPTH-radius;
                v.z = - v.z ;
            }

            if (pos.x < radius){
                pos.x = radius;
                v.x = - v.x ;
            }

            if (pos.y < radius){
                pos.y = radius;
                v.y = - v.y ;
            }

            if (pos.z < radius){
                pos.z = radius;
                v.z = -v.z ;
            }
    }        
}




void main()
{
    Nucleon nucleon_i;
    vec3 pos_i,pos_j, v_i, v_j;
    float r;   //distance between nucleons
    vec3 delta;  //coordinates delta
    float f1,f2,f3;
    vec3 F;
    nucleon_i = In.nucleons[i];
    pos_i= nucleon_i.pos.xyz;

    if (stage==1){ //calc near nucleons  and far field
        int index = 0;
        F = vec3(0,0,0);
        for (int j=0;j<In.nucleons.length();j++){
            if (i == j) continue;
            r = distance(pos_i, In.nucleons[j].pos.xyz);
            if (r==0) continue;
            if (r<NEARDIST){
                Near.indexes[i][index+1]=j;
                index++;
            }
            else {  //far field
                delta = In.nucleons[i].pos.xyz - In.nucleons[j].pos.xyz;
                f1= In.nucleons[i].q*In.nucleons[j].q*INTERACT_KOEFF/r;
                F += f1 * delta/r;  
            }

        }
        Near.indexes[i][0]=index;  // near nucleons count
        Far.F.xyz = F;
        return;
    }

    v_i = nucleon_i.v.xyz;
    //In.nucleons[i].pos.x +=rand(nucleon_i.pos.yz);

    F = vec3(0.0,0.0,0.0);
    vec4 totalrot = vec4(0.0, 0.0, 0.0, 1.0);

//  animate
    if (nucleon_i.animate >0) nucleon_i.animate-=1;
  

    for (int jj=1;jj<=Near.indexes[i][0];jj++){
        int j = Near.indexes[i][jj];
        //if (i == j) continue;
        Nucleon nucleon_j = In.nucleons[j];
        pos_j = nucleon_j.pos.xyz;
        delta = pos_i - pos_j;
        r = distance(pos_i, pos_j);
        if (r==0) continue;
        
        f1= nucleon_i.q*nucleon_j.q*INTERACT_KOEFF/r;
        F += delta/r*f1;  
        if (r<40) {             
             f2 = 0;
             float sumradius = nucleon_i.r + nucleon_j.r;
             if (r<(sumradius+REPULSIOND))
                f2 = 1/r*  REPULSION_KOEFF1;
             else if ( (sumradius-ATTRACTIOND)<r && r<(sumradius+ATTRACTIOND)){
                if (atype==1){
                    float x = r - sumradius;
                    f2 = -ATTRACT_KOEFF*x;  
                }
                else {
                    float x = r - sumradius;
                    f2 = -ATTRACT_KOEFF*x;  
                    f2 += -0.1*r;  
                }
             }

                
             F += delta/r*f2;
        } 

    } //forj
    
    nucleon_i.rotv = totalrot;


 // mixer
    if (nucleon_i.type==100){
        if (v_i!= vec3(0.0,0.0,0.0))
            v_i = normalize(v_i);
    }

//heating
   v_i +=  v_i * HEAT*0.001;      
 
 //gravity
   if (gravity==1) v_i.y -= 0.001; //gravity
     
//shake
   if (shake==1) v_i+= vec3(rand(pos_i.xy)-0.5,rand(pos_i.xz)-0.5,rand(pos_i.yz)-0.5)*0.03;

// far field
   //F += Far.F.xyz*0.01;

//next
    v_i += F/(nucleon_i.m*MASS_KOEFF);
    pos_i += v_i;
    nucleon_i.rot = normalize(qmul(nucleon_i.rotv,nucleon_i.rot));
    
//limits    
    limits(pos_i,v_i,nucleon_i.r); //borders of container
    

    nucleon_i.v.xyz = v_i;
    nucleon_i.pos.xyz = pos_i;
    Out.nucleons[i] = nucleon_i;
}