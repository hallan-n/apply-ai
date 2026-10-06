from sqlalchemy import Boolean, Integer, String, Text, select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

DATABASE_URL = "sqlite+aiosqlite:///jobs.db"

engine = create_async_engine(DATABASE_URL)
Session = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_id: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    company: Mapped[str] = mapped_column(String)
    job_title: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String, default="pending")
    location: Mapped[str] = mapped_column(String)
    is_remote: Mapped[bool] = mapped_column(Boolean, default=False)


async def create_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def create_job(
    job_id,
    company,
    job_title,
    description,
    location,
    status="pending",
    is_remote=False,
):
    async with Session() as db:

        job = Job(
            job_id=job_id,
            company=company,
            job_title=job_title,
            description=description,
            status=status,
            location=location,
            is_remote=is_remote,
        )

        db.add(job)
        await db.commit()

        return job


async def get_job(job_id):
    async with Session() as db:

        result = await db.execute(select(Job).where(Job.job_id == job_id))

        return result.scalar_one_or_none()


async def get_jobs():
    async with Session() as db:

        result = await db.execute(select(Job))

        return result.scalars().all()


async def update_job_status(job_id, status):
    async with Session() as db:

        result = await db.execute(select(Job).where(Job.job_id == job_id))

        job = result.scalar_one_or_none()

        if not job:
            return False

        job.status = status

        await db.commit()

        return True


async def delete_job(job_id):
    async with Session() as db:

        result = await db.execute(select(Job).where(Job.job_id == job_id))

        job = result.scalar_one_or_none()

        if not job:
            return False

        await db.delete(job)
        await db.commit()

        return True
