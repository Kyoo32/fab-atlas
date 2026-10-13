import { defineCollection } from 'astro:content';
import { z } from 'astro/zod';
import { docsLoader } from '@astrojs/starlight/loaders';
import { docsSchema } from '@astrojs/starlight/schema';

// 작업일지(notes/devlog)용 필드. 다른 문서에서는 비워 둬도 돼요.
const notesFields = z.object({
	date: z.coerce.date().optional(),
	summary: z.string().optional(),
	tags: z.array(z.string()).default([]),
	hours: z.number().nullable().optional(),
});

export const collections = {
	docs: defineCollection({ loader: docsLoader(), schema: docsSchema({ extend: notesFields }) }),
};
