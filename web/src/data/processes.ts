// 8대 공정 목록. 홈의 공정 띠와 sources.csv의 process 값이 이 목록을 따라요.
export const PROCESSES = [
	{ id: 'wafer', name: '웨이퍼 제조' },
	{ id: 'oxidation', name: '산화' },
	{ id: 'photo', name: '포토' },
	{ id: 'etch', name: '식각' },
	{ id: 'deposition-implant', name: '증착·이온주입' },
	{ id: 'metallization', name: '금속배선' },
	{ id: 'eds', name: 'EDS' },
	{ id: 'packaging', name: '패키징' },
] as const;

export type Process = (typeof PROCESSES)[number];
