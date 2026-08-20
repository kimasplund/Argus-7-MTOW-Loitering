// ARGUS-7 persistent comms-relay UAV — parametric model
// MTOW 250 kg | span 9.26 m | S 3.9 m2 | AR 22.0 | MAC 0.421 m
$fn = 48;
span = 9.263; c_root = 0.674; c_tip = 0.303; t_ratio = 0.12;
fuse_l = 3.4; fuse_r = 0.24;
boom_l = 3.2; tail_arm = 3.2;
S_h = 0.309; S_v = 0.451;

module halfwing() {
    hull() {
        translate([0,0,0]) scale([c_root/4, c_root*t_ratio/2, c_root/4]) sphere(1);
        translate([0,span/2-0.05,0.12]) scale([c_tip/4, max(c_tip*t_ratio/2,0.02), c_tip/4]) sphere(1);
    }
}
module boom(x) { translate([x, -0.2, 0]) rotate([-90,0,0]) cylinder(d=0.09, h=boom_l); }
module vtail_fin(x, mirror_) {
    translate([x, -boom_l-0.15, 0.05])
    rotate([0, mirror_ ? -42 : 42, 0])
    scale([1, 1, 0.08])
    linear_extrude(0.02)
        polygon([[0,0],[sqrt(S_h/2),0],[sqrt(S_h/2)*0.55,0.42],[0,0.30]]);
}
// fuselage pod
hull() {
    translate([0,-0.4,0]) sphere(fuse_r);
    translate([0,-fuse_l*0.55,0]) sphere(fuse_r*0.9);
    translate([0,-fuse_l+0.25,0.02]) sphere(fuse_r*0.55);  // engine taper
}
// EO/IR gimbal ball (chin)
translate([0,-0.62,-fuse_r-0.02]) sphere(0.15);
// parachute bay hump
translate([0,-1.1,fuse_r*0.8]) scale([1,1.6,0.7]) sphere(0.14);
// wing
translate([0,-0.72,0.10]) { halfwing(); mirror([0,1,0]) halfwing(); }
// twin booms + pusher prop
boom(0.62); mirror([1,0,0]) boom(0.62);
translate([0,-fuse_l-0.05,0.02]) rotate([90,0,0]) { cylinder(d=0.10,h=0.12);
    translate([0,0,0.10]) scale([1,0.06,0.02]) sphere(0.405); }  // 32" prop disc
// inverted-V tail
vtail_fin(0.62,false); vtail_fin(-0.62,true);
// comms antenna blade
translate([0,-1.5,-fuse_r-0.06]) scale([0.01,0.18,0.10]) cube(1,center=true);
