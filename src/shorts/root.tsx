import React from 'react';
import {CalculateMetadataFunction, Composition} from 'remotion';
import {
  EnglishListeningRoomShort,
  EnglishListeningRoomShortProps,
} from './english-listening-room-short';

const defaultProps: EnglishListeningRoomShortProps = {
  shortId: 'elr-s-000',
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
