import React from 'react';
import {CalculateMetadataFunction, Composition} from 'remotion';
import {
  EnglishListeningRoomShort,
  EnglishListeningRoomShortProps,
} from './english-listening-room-short';

const defaultProps: EnglishListeningRoomShortProps = {
  format: 'micro_story',
  cefr: 'A2',
  durationSec: 30,
  hook: 'Can you understand this short English story?',
  hookEndSec: 1.5,
  scenes: [
    {
      speaker: 'narrator',
      text: 'A small moment can become a useful listening lesson.',
      startSec: 1.5,
      endSec: 21,
    },
  ],
  prompt: 'What did you hear?',
  answer: 'You heard a short English story.',
  promptStartSec: 21,
  answerStartSec: 26,
  backgroundImage: 'shorts/elr-s-001/story-background-v2.png',
  brandLogo: 'branding/english_listening_room_avatar_v2.png',
  cta: 'Subscribe for your next listening story.',
};

const calculateMetadata: CalculateMetadataFunction<EnglishListeningRoomShortProps> = ({props}) => ({
  durationInFrames: Math.ceil(props.durationSec * 30),
});

export const ShortsRoot: React.FC = () => (
  <Composition
    id="EnglishListeningRoomShort"
    component={EnglishListeningRoomShort}
    durationInFrames={900}
    fps={30}
    width={1080}
    height={1920}
    defaultProps={defaultProps}
    calculateMetadata={calculateMetadata}
  />
);
