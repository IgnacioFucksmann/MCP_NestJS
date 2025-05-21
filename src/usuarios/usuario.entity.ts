import { Entity, Column, PrimaryGeneratedColumn } from 'typeorm';
import { ApiProperty } from '@nestjs/swagger';

@Entity('usuario')
export class Usuario {
  @PrimaryGeneratedColumn()
  @ApiProperty({ description: 'ID único del usuario' })
  id: number;

  @Column({ type: 'character varying', length: 100 })
  @ApiProperty({ description: 'Nombre del usuario', maxLength: 100 })
  nombre: string;

  @Column({ type: 'character varying', length: 100 })
  @ApiProperty({ description: 'Correo electrónico del usuario', maxLength: 100 })
  email: string;

  @Column({ type: 'character varying', length: 255 })
  @ApiProperty({ description: 'Contraseña del usuario', maxLength: 255 })
  password: string;
} 