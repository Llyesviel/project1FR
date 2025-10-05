import React, { useRef, useEffect } from 'react';
import * as THREE from 'three';

interface PlasmaBackgroundProps {
  color?: string;
  speed?: number;
  direction?: 'forward' | 'reverse' | 'pingpong';
  scale?: number;
  opacity?: number;
  mouseInteractive?: boolean;
  style?: React.CSSProperties;
  className?: string;
}

const PlasmaBackground: React.FC<PlasmaBackgroundProps> = ({
  color,
  speed = 1.0,
  direction = 'forward',
  scale = 1.0,
  opacity = 1.0,
  mouseInteractive = false,
  style,
  className,
}) => {
  const mountRef = useRef<HTMLDivElement>(null);
  const sceneRef = useRef<THREE.Scene>();
  const rendererRef = useRef<THREE.WebGLRenderer>();
  const cameraRef = useRef<THREE.OrthographicCamera>();
  const materialRef = useRef<THREE.ShaderMaterial>();
  const animationIdRef = useRef<number>();
  const mouseRef = useRef({ x: 0, y: 0 });
  const timeRef = useRef(0);

  const vertexShader = `
    varying vec2 vUv;
    void main() {
      vUv = uv;
      gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
    }
  `;

  const fragmentShader = `
    uniform float u_time;
    uniform vec2 u_resolution;
    uniform vec2 u_mouse;
    uniform float u_speed;
    uniform float u_scale;
    uniform float u_opacity;
    uniform vec3 u_color;
    varying vec2 vUv;

    void main() {
      vec2 st = vUv * u_scale;
      vec2 mouse = u_mouse * 0.5;
      
      float time = u_time * u_speed;
      
      // Plasma effect
      float plasma1 = sin(st.x * 10.0 + time) * 0.5 + 0.5;
      float plasma2 = sin(st.y * 10.0 + time * 1.2) * 0.5 + 0.5;
      float plasma3 = sin((st.x + st.y) * 8.0 + time * 0.8) * 0.5 + 0.5;
      float plasma4 = sin(sqrt(st.x * st.x + st.y * st.y) * 12.0 + time * 1.5) * 0.5 + 0.5;
      
      // Mouse interaction
      if (length(u_mouse) > 0.0) {
        float dist = distance(st, mouse);
        plasma1 += sin(dist * 20.0 - time * 3.0) * 0.1;
        plasma2 += cos(dist * 15.0 - time * 2.5) * 0.1;
      }
      
      float plasma = (plasma1 + plasma2 + plasma3 + plasma4) * 0.25;
      
      // Color mapping
      vec3 color1 = vec3(0.8, 0.2, 0.1); // Orange-red
      vec3 color2 = vec3(0.9, 0.5, 0.2); // Orange
      vec3 color3 = vec3(0.1, 0.1, 0.3); // Dark blue
      
      vec3 finalColor;
      if (length(u_color) > 0.0) {
        finalColor = mix(u_color * 0.5, u_color, plasma);
      } else {
        finalColor = mix(mix(color3, color1, plasma), color2, sin(plasma * 3.14159) * 0.5 + 0.5);
      }
      
      gl_FragColor = vec4(finalColor, u_opacity);
    }
  `;

  useEffect(() => {
    if (!mountRef.current) return;

    // Scene setup
    const scene = new THREE.Scene();
    sceneRef.current = scene;

    // Camera setup
    const camera = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);
    cameraRef.current = camera;

    // Renderer setup
    const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
    renderer.setSize(mountRef.current.clientWidth, mountRef.current.clientHeight);
    renderer.setClearColor(0x000000, 0);
    rendererRef.current = renderer;

    mountRef.current.appendChild(renderer.domElement);

    // Shader material
    const material = new THREE.ShaderMaterial({
      vertexShader,
      fragmentShader,
      uniforms: {
        u_time: { value: 0 },
        u_resolution: { value: new THREE.Vector2(mountRef.current.clientWidth, mountRef.current.clientHeight) },
        u_mouse: { value: new THREE.Vector2(0, 0) },
        u_speed: { value: speed },
        u_scale: { value: scale },
        u_opacity: { value: opacity },
        u_color: { value: color ? new THREE.Color(color) : new THREE.Vector3(0, 0, 0) },
      },
      transparent: true,
    });
    materialRef.current = material;

    // Geometry
    const geometry = new THREE.PlaneGeometry(2, 2);
    const mesh = new THREE.Mesh(geometry, material);
    scene.add(mesh);

    // Mouse interaction
    const handleMouseMove = (event: MouseEvent) => {
      if (!mouseInteractive || !mountRef.current) return;
      
      const rect = mountRef.current.getBoundingClientRect();
      mouseRef.current.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
      mouseRef.current.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
      
      if (materialRef.current) {
        materialRef.current.uniforms.u_mouse.value.set(mouseRef.current.x, mouseRef.current.y);
      }
    };

    if (mouseInteractive) {
      mountRef.current.addEventListener('mousemove', handleMouseMove);
    }

    // Animation loop
    const animate = () => {
      timeRef.current += 0.01;
      
      let currentTime = timeRef.current;
      if (direction === 'reverse') {
        currentTime = -timeRef.current;
      } else if (direction === 'pingpong') {
        currentTime = Math.sin(timeRef.current * 0.5) * 2;
      }
      
      if (materialRef.current) {
        materialRef.current.uniforms.u_time.value = currentTime;
        materialRef.current.uniforms.u_speed.value = speed;
        materialRef.current.uniforms.u_scale.value = scale;
        materialRef.current.uniforms.u_opacity.value = opacity;
        if (color) {
          materialRef.current.uniforms.u_color.value = new THREE.Color(color);
        }
      }
      
      renderer.render(scene, camera);
      animationIdRef.current = requestAnimationFrame(animate);
    };

    animate();

    // Resize handler
    const handleResize = () => {
      if (!mountRef.current || !renderer || !material) return;
      
      const width = mountRef.current.clientWidth;
      const height = mountRef.current.clientHeight;
      
      renderer.setSize(width, height);
      material.uniforms.u_resolution.value.set(width, height);
    };

    window.addEventListener('resize', handleResize);

    return () => {
      if (animationIdRef.current) {
        cancelAnimationFrame(animationIdRef.current);
      }
      if (mountRef.current && renderer.domElement) {
        mountRef.current.removeChild(renderer.domElement);
      }
      if (mouseInteractive && mountRef.current) {
        mountRef.current.removeEventListener('mousemove', handleMouseMove);
      }
      window.removeEventListener('resize', handleResize);
      renderer.dispose();
    };
  }, [color, speed, direction, scale, opacity, mouseInteractive]);

  return (
    <div
      ref={mountRef}
      className={className}
      style={{
        width: '100%',
        height: '100%',
        position: 'absolute',
        top: 0,
        left: 0,
        zIndex: 0,
        ...style,
      }}
    />
  );
};

export default PlasmaBackground;