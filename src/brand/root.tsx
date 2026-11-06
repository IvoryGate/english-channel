import {Composition} from 'remotion';
import {EnglishListeningRoomIntro} from './english-listening-room-intro';
import {EnglishListeningRoomOutro} from './english-listening-room-outro';
import {EnglishListeningRoomIntroV4, EnglishListeningRoomOutroV4, motionBrandDefaults, motionBrandSchema} from './motion-v4';
import motionSpec from '../../configs/branding/motion-v4.json';

export const BrandRoot = () => {
  return (
    <>
    <Composition id="EnglishListeningRoomIntroV4" component={EnglishListeningRoomIntroV4}
      durationInFrames={motionSpec.introFrames} fps={motionSpec.fps} width={1920} height={1080}
      schema={motionBrandSchema} defaultProps={motionBrandDefaults} />
    <Composition id="EnglishListeningRoomOutroV4" component={EnglishListeningRoomOutroV4}
      durationInFrames={motionSpec.outroFrames} fps={motionSpec.fps} width={1920} height={1080}
      schema={motionBrandSchema} defaultProps={motionBrandDefaults} />
    <Composition
      id="EnglishListeningRoomIntro"
      component={EnglishListeningRoomIntro}
      durationInFrames={250}
      fps={30}
      width={1920}
      height={1080}
    />
    <Composition
      id="EnglishListeningRoomOutro"
      component={EnglishListeningRoomOutro}
      durationInFrames={250}
      fps={30}
      width={1920}
      height={1080}
    />
    </>
  );
};
