declare module '../../../scripts/generate-checksums' {
    export function calculateChecksum(filePath: string): Promise<string>;
    export function shouldIncludeFile(filename: string): boolean;
    export function generateChecksums(dir: string): Promise<Array<{ file: string; checksum: string }>>;
    export function writeChecksumsFile(checksums: Array<{ file: string; checksum: string }>, outputPath: string): void;
}
