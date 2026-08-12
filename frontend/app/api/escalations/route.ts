import { NextResponse } from 'next/server';
import { exec } from 'child_process';
import path from 'path';
import { promisify } from 'util';

const execPromise = promisify(exec);

export const revalidate = 0;

export async function GET() {
  try {
    const backendDir = path.join(process.cwd(), '..', 'backend');
    const { stdout } = await execPromise('uv run python src/get_escalations.py', {
      cwd: backendDir,
    });
    const escalations = JSON.parse(stdout.trim());
    return NextResponse.json(escalations);
  } catch (error) {
    console.error('Failed to get escalations:', error);
    return NextResponse.json({ error: 'Failed to fetch escalations' }, { status: 500 });
  }
}
