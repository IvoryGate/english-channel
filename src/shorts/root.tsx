import React from 'react';
import {CalculateMetadataFunction, Composition, Still} from 'remotion';
import {z} from 'zod';
import {
  EnglishListeningRoomShort,
  EnglishListeningRoomShortProps,
} from './english-listening-room-short';
import {
  EnglishListeningRoomShortThumbnail,
  EnglishListeningRoomShortThumbnailProps,
} from './english-listening-room-short-thumbnail';

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

const shortSchema = z.object({
  format: z.enum(['micro_story', 'listen_choose', 'dialogue', 'classic_cliffhanger']),
  cefr: z.enum(['A2', 'B1']), durationSec: z.number().positive(),
  hook: z.string(), hookEndSec: z.number(), prompt: z.string(), answer: z.string(),
  promptStartSec: z.number(), answerStartSec: z.number(),
  backgroundImage: z.string(), brandLogo: z.string(), cta: z.string(),
  scenes: z.array(z.object({speaker: z.string(), text: z.string(), startSec: z.number(), endSec: z.number(),
    caption: z.object({text: z.string(), startMs: z.number(), endMs: z.number(),
      timestampMs: z.number().nullable(), confidence: z.number().nullable()}).optional()})),
  spectrum: z.object({fps: z.number().positive(), frames: z.array(z.array(z.number())),
    threads: z.array(z.array(z.number())), particles: z.array(z.array(z.array(z.number()))),
    sourceSha256: z.string().optional()}).optional(),
});

const defaultThumbnailProps: EnglishListeningRoomShortThumbnailProps = {
  format: 'listen_choose',
  cefr: 'A2',
  headline: 'Fifteen or Fifty?',
  backgroundImage: 'shorts/elr-s-001/story-background-v2.png',
  brandLogo: 'branding/english_listening_room_avatar_v2.png',
};

export const ShortsRoot: React.FC = () => (
  <>
    <Composition
      id="EnglishListeningRoomShort"
      component={EnglishListeningRoomShort}
      schema={shortSchema}
      durationInFrames={900}
      fps={30}
      width={1080}
      height={1920}
      defaultProps={defaultProps}
      calculateMetadata={calculateMetadata}
    />
    <Still
      id="EnglishListeningRoomShortThumbnail"
      component={EnglishListeningRoomShortThumbnail}
      width={1080}
      height={1920}
      defaultProps={defaultThumbnailProps}
    />
  </>
);
