import { defineCollection } from 'astro:content';
import { z } from 'astro/zod';
import { docsLoader, i18nLoader } from '@astrojs/starlight/loaders';
import { docsSchema, i18nSchema } from '@astrojs/starlight/schema';

// 작업일지(notes/devlog)용 필드. 다른 문서에서는 비워 둬도 돼요.
const notesFields = z.object({
	date: z.coerce.date().optional(),
	summary: z.string().optional(),
	tags: z.array(z.string()).default([]),
	hours: z.number().nullable().optional(),
});

export const collections = {
	docs: defineCollection({ loader: docsLoader(), schema: docsSchema({ extend: notesFields }) }),
	// Starlight UI 문구 덮어쓰기용. 지금은 비어 있어요(src/content/i18n/ko.json).
	i18n: defineCollection({ loader: i18nLoader(), schema: i18nSchema() }),
};
