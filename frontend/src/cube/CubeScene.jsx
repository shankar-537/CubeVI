import { forwardRef } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls } from '@react-three/drei';
import Cube from './Cube';

// Camera, lights and mouse rotation around the cube.
const CubeScene = forwardRef(function CubeScene(props, ref) {
  return (
    <Canvas camera={{ position: [4.2, 3.6, 5.6], fov: 38 }}>
      <ambientLight intensity={1.5} />
      <directionalLight position={[5, 8, 6]} intensity={0.9} />
      <directionalLight position={[-6, -4, -5]} intensity={0.3} />
      <Cube ref={ref} {...props} />
      <OrbitControls
        makeDefault
        enablePan={false}
        enableDamping
        minDistance={5}
        maxDistance={12}
      />
    </Canvas>
  );
});

export default CubeScene;
