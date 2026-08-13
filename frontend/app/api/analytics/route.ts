import { NextResponse } from 'next/server';
import { exec } from 'child_process';
import path from 'path';
import { promisify } from 'util';

const execPromise = promisify(exec);

export const revalidate = 0;

export async function GET() {
  try {
    const backendDir = path.join(process.cwd(), '..', 'backend');
    const { stdout } = await execPromise('uv run python src/get_analytics.py', {
      cwd: backendDir,
    });
    const analytics = JSON.parse(stdout.trim());
    return NextResponse.json(analytics);
  } catch (error) {
    console.error('Failed to get analytics:', error);
    return NextResponse.json({ error: 'Failed to fetch analytics' }, { status: 500 });
  }
}
