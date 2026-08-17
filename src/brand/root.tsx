import {Composition} from 'remotion';
import {EnglishListeningRoomIntro} from './english-listening-room-intro';
import {EnglishListeningRoomOutro} from './english-listening-room-outro';

export const BrandRoot = () => {
  return (
    <>
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
